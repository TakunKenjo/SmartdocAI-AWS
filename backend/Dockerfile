FROM public.ecr.aws/lambda/python:3.11

# Nâng cấp pip lên phiên bản mới nhất
RUN pip install --upgrade pip --no-cache-dir

# Sao chép requirements.txt vào task root của Lambda
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Cài đặt các package Python
RUN pip install -r requirements.txt \
    --prefer-binary \
    --no-cache-dir \
    --target "${LAMBDA_TASK_ROOT}"

# Sao chép toàn bộ mã nguồn backend vào task root
COPY . ${LAMBDA_TASK_ROOT}

# Đảm bảo thư mục "static" tồn tại ngay tại build time (không thể tạo lúc runtime
# vì filesystem của Lambda là read-only, chỉ /tmp mới ghi được). "static/libs" bị
# .gitignore nên khi CodePipeline clone code sạch từ GitHub, COPY ở trên không tạo
# ra thư mục này -> phải tự mkdir ở đây để StaticFiles() không raise lỗi lúc import.
RUN mkdir -p "${LAMBDA_TASK_ROOT}/static"

# Thiết lập Lambda Handler làm lệnh mặc định của container
CMD [ "app_api.handler" ]

