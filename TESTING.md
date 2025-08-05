# Testing

1. Start the machine on the Azure web page: https://portal.azure.com/#@markgoplayfully.onmicrosoft.com/resource/subscriptions/475898f6-5209-4a73-b15e-0def24a9473f/resourcegroups/gpu2_group/providers/Microsoft.Compute/virtualMachines/holo/overview
2. start the vllm service

```bash
ssh -i ~/.ssh/id_ed25519 mrisher@172.173.228.133
docker run -it --gpus=all --rm -p 8000:8000 vllm/vllm-openai:v0.9.1     --model HCompany/Holo1-7B     --dtype bfloat16     --gpu-memory-utilization 0.9     --limit-mm-per-prompt 'image=3,video=0'     --mm-processor-kwargs '{"max_pixels": 1003520}'     --max-model-len 16384
```

3. To test localization, we created a script that loads a static HTML file.

Run it with

```bash
python test_click_reliability.py --base_url_localization http://172.173.228.133:8000/v1
```

# Notes:

Tweaking the prompt to only mention `NOT_FOUND` seemed to work for the test (which is bizarre)
But the `launch.sh` is no longer pulling screenshots; maybe we broke something.
