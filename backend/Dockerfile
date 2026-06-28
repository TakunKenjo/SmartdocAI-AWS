FROM public.ecr.aws/lambda/python:3.11

# Nâng cấp pip lên phiên bản mới nhất
RUN pip install --upgrade pip --no-cache-dir

# Sao chép requirements.txt vào task root của Lambda
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Cài đặt torch CPU-only và các package khác trong một lệnh duy nhất
# Sử dụng --extra-index-url để pip giải quyết dependency đúng bản torch CPU-only (+cpu),
# ngăn chặn việc tải về các thư viện CUDA/GPU nặng nề của NVIDIA.
RUN pip install torch==2.6.0+cpu -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    --prefer-binary \
    --no-cache-dir \
    --target "${LAMBDA_TASK_ROOT}"

# Bước dọn dẹp dự phòng để xóa triệt để thư viện CUDA/GPU nếu có package nào cố tình kéo thêm
RUN rm -rf ${LAMBDA_TASK_ROOT}/nvidia* \
           ${LAMBDA_TASK_ROOT}/triton* \
           ${LAMBDA_TASK_ROOT}/cusparselt*

# Pre-download model embedding LaBSE vào image để tránh download lúc cold start
RUN HF_HOME=/var/task/hf_cache \
    TRANSFORMERS_CACHE=/var/task/hf_cache \
    python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/LaBSE')"

# Sao chép toàn bộ mã nguồn backend vào task root
COPY . ${LAMBDA_TASK_ROOT}

# Thiết lập Lambda Handler làm lệnh mặc định của container
CMD [ "app_api.handler" ]
