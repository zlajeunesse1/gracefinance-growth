FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Product decision: keep the legacy X growth code available for reference,
# but never start its posting/polling scheduler in a deployed container.
CMD ["python", "-c", "print('GraceFinance X growth worker disabled by product decision')"]
