ARG BASE_IMAGE=lmsysorg/sglang@sha256:5fc09edb6a0bb1d5b6992b543723c66d08f86d7a507e951e87e0d05db4ac766e
FROM ${BASE_IMAGE} AS builder
ARG SAGE_COMMIT=d1a57a546c3d395b1ffcbeecc66d81db76f3b4b5
ENV TORCH_CUDA_ARCH_LIST=12.0 MAX_JOBS=8 EXT_PARALLEL=1
RUN command -v nvcc && command -v g++ && command -v git \
    && python3 -c "import torch; print('Building against', torch.__version__, torch.version.cuda)"
RUN python3 -m pip install --no-cache-dir ninja packaging wheel
WORKDIR /build/SageAttention
RUN git init . && git remote add origin https://github.com/thu-ml/SageAttention.git \
    && git fetch --depth 1 origin "${SAGE_COMMIT}" && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "${SAGE_COMMIT}"
# Patch both host C++ and nvcc flags for the PyTorch headers in the base image.
RUN python3 -c "from pathlib import Path; p=Path('setup.py'); s=p.read_text(); assert s.count('-std=c++17') == 2; p.write_text(s.replace('-std=c++17', '-std=c++20'))" \
    && python3 -m pip wheel . --no-build-isolation --no-deps --wheel-dir /wheels \
    && cp LICENSE /wheels/SageAttention-LICENSE

FROM ${BASE_IMAGE}
ARG BASE_IMAGE
ARG SAGE_COMMIT=d1a57a546c3d395b1ffcbeecc66d81db76f3b4b5
ENV SGLANG_CACHE_DIT_ENABLED=false
LABEL org.opencontainers.image.title="SGLang MiniMax H3 with SageAttention SM120" \
      org.opencontainers.image.base.name="${BASE_IMAGE}" \
      ai.nbis-h3.sageattention.commit="${SAGE_COMMIT}" \
      ai.nbis-h3.cuda.arch="12.0" \
      ai.nbis-h3.cpp.standard="20"
COPY --from=builder /wheels /opt/nbis-h3/wheels
RUN python3 -m pip install --no-cache-dir --no-deps --force-reinstall /opt/nbis-h3/wheels/sageattention-*.whl \
    && python3 -m pip install --no-cache-dir --no-deps comfy-kitchen==0.2.40
COPY smoke-test.py /opt/nbis-h3/smoke-test.py
COPY serve-h3.sh /usr/local/bin/h3-serve
RUN chmod 755 /usr/local/bin/h3-serve \
    && python3 /opt/nbis-h3/smoke-test.py
