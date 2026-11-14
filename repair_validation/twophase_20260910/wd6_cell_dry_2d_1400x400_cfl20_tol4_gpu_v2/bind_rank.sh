#!/bin/bash
devices=(1)
export CUDA_VISIBLE_DEVICES=${devices[$OMPI_COMM_WORLD_LOCAL_RANK]}
exec "$@"
