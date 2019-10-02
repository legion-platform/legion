# Base image name
FROM {{ base_image }}

{{ conda_installation_content }}

WORKDIR /app

# Copying of dependencies
COPY {{ conda_file_name }} \
     .

# Creation of conda's envinroment named model
RUN conda create -vv --name {{ conda_env_name }} --yes && \
    conda env update --name={{ conda_env_name }} --file={{ conda_file_name }}

# Updating PATH for entrypoint
ENV PATH /opt/conda/envs/{{ conda_env_name }}/bin:$PATH

ENV LEGION_MODEL_NAME {{ model_name }}
ENV LEGION_MODEL_VERSION {{ model_version }}

# Installing of additional software inside specified env
RUN /opt/conda/envs/{{ conda_env_name }}/bin/pip install gunicorn[gevent]


# Copy wrappers
COPY {{ entrypoint_target }} \
     {{ entrypoint_docker }} \
     {{ handler_file }} \
     ./

# Copy model only
COPY {{ model_location }} /app/{{ model_location }}

# Exposing HTTP port
EXPOSE {{ port }}

# Change permissions to cmd
RUN chmod +x {{ entrypoint_docker }}

# Setting cmd
ENTRYPOINT ["bash", "-c"]
CMD ["/app/{{ entrypoint_docker }}"]
