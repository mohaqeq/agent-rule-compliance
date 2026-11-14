# statsmodels for studya_eval.py's mixed-effects model. The script itself (research/harness/studya_mixed.py) is mounted
# at run time by studya_eval.py, so the image only holds the libraries.
#   docker build -t ucn-studya-stats research/trials/containers/stats
FROM python:3.12-slim
RUN pip install --no-cache-dir numpy==2.1.3 pandas==2.2.3 scipy==1.14.1 statsmodels==0.14.4
ENTRYPOINT ["python", "/studya_mixed.py"]
