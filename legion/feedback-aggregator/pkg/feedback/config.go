package feedback

import (
	"fmt"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	logf "sigs.k8s.io/controller-runtime/pkg/runtime/log"
)

const (
	CfgFluentdHost          = "fluentd.host"
	CfgFluentdPort          = "fluentd.port"
	CfgProhibitedHeaders    = "prohibited_headers"
	CfgRequestResponseTag   = "tags.request_response"
	CfgResponseBodyTag      = "tags.response_body"
	CfgFeedbackTag          = "tags.feedback"
	defaultConfigPathForDev = "legion/feedback-aggregator"
	cmdProhibitedHeaders    = "prohibited-headers"
	cmdFluentHost           = "fluentd-host"
	cmdFluentdPort          = "fluentd-port"
)

var (
	CfgFile string
	logC    = logf.Log.WithName("config")
)

func InitBasicParams(cmd *cobra.Command) {
	setUpLogger()
	cobra.OnInitialize(initConfig)

	cmd.Flags().StringVar(&CfgFile, "config", "", "config file")
	cmd.Flags().String(cmdFluentHost, "127.0.0.1", "Fluentd host")
	cmd.Flags().Int(cmdFluentdPort, 24224, "Fluentd port")
	cmd.Flags().StringSlice(
		cmdProhibitedHeaders,
		[]string{},
		"List of prohibited headers which will be skipped from feedback",
	)

	PanicIfError(viper.BindPFlag(CfgFluentdHost, cmd.Flags().Lookup(cmdFluentHost)))
	PanicIfError(viper.BindPFlag(CfgFluentdPort, cmd.Flags().Lookup(cmdFluentdPort)))
	PanicIfError(viper.BindPFlag(CfgProhibitedHeaders, cmd.Flags().Lookup(cmdProhibitedHeaders)))

	viper.SetDefault(CfgProhibitedHeaders, []string{"authorization", "x-jwt", "x-user", "x-email"})
	viper.SetDefault(CfgRequestResponseTag, "request_response")
	viper.SetDefault(CfgResponseBodyTag, "response_body")
	viper.SetDefault(CfgFeedbackTag, "feedback")
}

func PanicIfError(err error) {
	if err != nil {
		panic(err)
	}
}

func initConfig() {
	if CfgFile != "" {
		viper.SetConfigFile(CfgFile)
	} else {
		viper.AddConfigPath(defaultConfigPathForDev)
	}

	if err := viper.ReadInConfig(); err != nil {
		logC.Info(fmt.Sprintf("Error during reading of the config: %s", err.Error()))
	}
}

func setUpLogger() {
	logf.SetLogger(logf.ZapLoggerTo(os.Stdout, true))
}
