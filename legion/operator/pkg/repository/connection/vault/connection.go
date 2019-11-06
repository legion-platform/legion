package vault

import (
	"encoding/json"
	"net/http"
	"path"

	bank_vaults "github.com/banzaicloud/bank-vaults/pkg/vault"
	vaultapi "github.com/hashicorp/vault/api"
	"github.com/legion-platform/legion/legion/operator/pkg/apis/connection"
	conn_config "github.com/legion-platform/legion/legion/operator/pkg/config/connection"
	legion_errors "github.com/legion-platform/legion/legion/operator/pkg/errors"
	conn_repository "github.com/legion-platform/legion/legion/operator/pkg/repository/connection"
	"github.com/spf13/viper"
)

const (
	ConnKey          = "legion_conn"
	ConnectionIdsKey = "keys"
)

var (
	MaxSize   = 500
	FirstPage = 0
)

// Could be used for storing sensitive data
// TODO: Remove the token after implementation of the issue https://github.com/legion-platform/legion/issues/1008
type vaultConnRepository struct {
	vaultClient         *vaultapi.Client
	connectionVaultPath string
	connDecryptToken    string
}

func NewRepository(
	vaultClient *vaultapi.Client,
	connectionVaultPath string,
	connDecryptToken string,
) conn_repository.Repository {
	return &vaultConnRepository{
		vaultClient:         vaultClient,
		connectionVaultPath: connectionVaultPath,
		connDecryptToken:    connDecryptToken,
	}
}

func NewRepositoryFromConfig() (conn_repository.Repository, error) {
	vConfig := vaultapi.DefaultConfig()
	vConfig.Address = viper.GetString(conn_config.VaultURL)

	vClient, err := vaultapi.NewClient(vConfig)
	if err != nil {
		return nil, err
	}
	vClient.SetToken(viper.GetString(conn_config.VaultToken))
	// This client provides authentication using k8s api
	_, err = bank_vaults.NewClientFromRawClient(
		vClient,
		bank_vaults.ClientRole(viper.GetString(conn_config.VaultRole)),
	)

	return NewRepository(
		vClient,
		viper.GetString(conn_config.VaultSecretEnginePath),
		viper.GetString(conn_config.DecryptToken),
	), err
}

func (vcr *vaultConnRepository) GetConnection(connID string) (*connection.Connection, error) {
	conn, err := vcr.getConnectionFromVault(connID)
	if err != nil {
		return nil, err
	}

	return conn.DeleteSensitiveData(), nil
}

func (vcr *vaultConnRepository) GetDecryptedConnection(
	connID string, connDecryptToken string,
) (*connection.Connection, error) {
	if connDecryptToken != vcr.connDecryptToken {
		return nil, legion_errors.ForbiddenError{}
	}

	return vcr.getConnectionFromVault(connID)
}

func (vcr *vaultConnRepository) GetConnectionList(
	options ...conn_repository.ListOption,
) ([]connection.Connection, error) {
	list, err := vcr.vaultClient.Logical().List(vcr.connectionVaultPath)
	if err != nil {
		return nil, convertVaultErrToLegionErr(err)
	}

	if list == nil {
		return []connection.Connection{}, nil
	}

	connectionIdsRaw, ok := list.Data[ConnectionIdsKey]
	if !ok {
		return nil, legion_errors.SerializationError{}
	}

	connectionIds, ok := connectionIdsRaw.([]interface{})
	if !ok {
		return nil, legion_errors.SerializationError{}
	}

	listOptions := &conn_repository.ListOptions{
		Filter: &conn_repository.Filter{},
		Page:   &FirstPage,
		Size:   &MaxSize,
	}
	for _, option := range options {
		option(listOptions)
	}

	connResults := []connection.Connection{}
	startPosition := *listOptions.Page * (*listOptions.Size)

	// TODO: think about more effective way to extract list of connections from vault in future
	// We assume that a connection is usually changed rarely.
	// So connection can not be deleted during this operation.
	for _, connIDRaw := range connectionIds[startPosition:] {
		if len(connResults) >= *listOptions.Size {
			break
		}

		connID, ok := connIDRaw.(string)
		if !ok {
			return nil, legion_errors.SerializationError{}
		}

		conn, err := vcr.GetConnection(connID)
		if err != nil {
			return nil, err
		}

		if len(listOptions.Filter.Type) == 0 {
			connResults = append(connResults, *conn)
		} else {
			for _, connType := range listOptions.Filter.Type {
				if connType == string(conn.Spec.Type) {
					connResults = append(connResults, *conn)
					continue
				}
			}
		}
	}

	return connResults, nil
}

func (vcr *vaultConnRepository) DeleteConnection(connID string) error {
	if _, err := vcr.GetConnection(connID); err != nil {
		return err
	}

	_, err := vcr.vaultClient.Logical().Delete(vcr.getFullPath(connID))

	return convertVaultErrToLegionErr(err)
}

func (vcr *vaultConnRepository) UpdateConnection(conn *connection.Connection) error {
	_, err := vcr.GetConnection(conn.ID)

	switch {
	case err == nil:
		// If err is not nil, then the connection already exists.
		return vcr.createOrUpdateConnection(conn)
	case legion_errors.IsNotFoundError(err):
		return legion_errors.NotFoundError{}
	default:
		return err
	}
}

func (vcr *vaultConnRepository) CreateConnection(conn *connection.Connection) error {
	_, err := vcr.GetConnection(conn.ID)

	switch {
	case err == nil:
		// If err is nil, then the connection already exists.
		return legion_errors.AlreadyExistError{}
	case legion_errors.IsNotFoundError(err):
		return vcr.createOrUpdateConnection(conn)
	default:
		return err
	}
}

func (vcr *vaultConnRepository) createOrUpdateConnection(conn *connection.Connection) error {
	_, err := vcr.vaultClient.Logical().Write(
		vcr.getFullPath(conn.ID),
		map[string]interface{}{
			ConnKey: conn,
		},
	)

	return convertVaultErrToLegionErr(err)
}

func (vcr *vaultConnRepository) getConnectionFromVault(connID string) (*connection.Connection, error) {
	vaultEntity, err := vcr.vaultClient.Logical().Read(vcr.getFullPath(connID))
	if err != nil {
		return nil, convertVaultErrToLegionErr(err)
	}

	// The vaultEntity is nil when binaryData is not located by specific connectionVaultPath
	if vaultEntity == nil {
		return nil, legion_errors.NotFoundError{}
	}

	binaryData, ok := vaultEntity.Data[ConnKey]
	if !ok {
		return nil, legion_errors.NotFoundError{}
	}

	connData, err := json.Marshal(binaryData)
	if err != nil {
		return nil, err
	}

	conn := &connection.Connection{}
	err = json.Unmarshal(connData, conn)
	if err != nil {
		return nil, legion_errors.SerializationError{}
	}

	return conn, nil
}

// Construct the full vault connectionVaultPath for legion connections
func (vcr *vaultConnRepository) getFullPath(connID string) (vaultPath string) {
	return path.Join(vcr.connectionVaultPath, connID)
}

func convertVaultErrToLegionErr(err error) error {
	if verr, ok := err.(*vaultapi.ResponseError); ok && verr.StatusCode == http.StatusForbidden {
		return legion_errors.ForbiddenError{}
	}

	return err
}
