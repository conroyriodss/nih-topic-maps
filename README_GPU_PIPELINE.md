GPU VM Pipeline for PROJECT_TERMS Embeddings

IMPORTANT: Dependencies are installed automatically during VM launch.
The script will verify all packages before proceeding.

Quick Start - Recommended

Run the complete pipeline:

  bash run_gpu_pipeline.sh

This will automatically:
1. Launch GPU VM with NVIDIA T4
2. Install CUDA drivers and Python packages
3. Verify all dependencies
4. Deploy embedding generation code
5. Run the job - takes 15-30 minutes
6. Auto-shutdown VM when complete

Estimated cost: about 25-50 cents total

Manual Step-by-Step

Step 1: Launch GPU VM and Install Dependencies

  bash launch_gpu_vm.sh

This will:
- Create the VM with GPU
- Install CUDA drivers
- Install Python packages: torch, transformers, google-cloud-bigquery, etc.
- Verify all installations
Takes about 3-5 minutes

Step 2: Deploy Code and Run

  bash deploy_and_run_embeddings.sh

Then start the job:

  VM_NAME="nih-embeddings-gpu-vm"
  ZONE="us-central1-a"
  gcloud compute ssh $VM_NAME --zone=$ZONE --command='nohup ~/nih-topic-maps/run_with_autoshutdown.sh > ~/embedding.log 2>&1 &'

Step 3: Monitor Progress

  bash monitor_gpu_vm.sh

Step 4: Check Results and Cleanup

  bash check_results_and_cleanup.sh

Troubleshooting

Problem: Dependencies not installed

If you see "ModuleNotFoundError: No module named google":

  bash fix_and_restart_vm.sh

This will reinstall all dependencies and restart the job.

Problem: GPU not detected

Check GPU status:

  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a --command='nvidia-smi'

If GPU is not ready, the code will run on CPU (slower but works).
Expected time: 15-30 min with GPU, 2-4 hours with CPU

Problem: VM will not launch

Check quotas:

  gcloud compute project-info describe --project=od-cl-odss-conroyri-f75a

Try different zone by editing launch_gpu_vm.sh and changing ZONE variable.

Problem: Job fails or hangs

SSH to VM to investigate:

  gcloud compute ssh nih-embeddings-gpu-vm --zone=us-central1-a

Check logs:

  tail -50 ~/embedding.log

Check processes:

  ps aux | grep python

Problem: VM will not auto-shutdown

Manually stop:

  bash emergency_stop_vm.sh

After Completion

Once embeddings are generated:

  python3 scripts/06_cluster_project_terms.py --k 100
  
  python3 scripts/compare_clustering_methods.py

Cost Estimate

- GPU VM with T4: about 50 cents per hour
- Expected runtime: 15-30 minutes with GPU, 2-4 hours with CPU
- Total cost: about 25-50 cents with GPU, 1-2 dollars with CPU

VM will auto-shutdown after completion to prevent runaway costs.

Dependency List

The following packages are automatically installed:
- CUDA drivers for NVIDIA T4 GPU
- Python 3 and pip
- pandas - data manipulation
- pyarrow - parquet file handling
- numpy - numerical computing
- torch - PyTorch for neural networks
- transformers - HuggingFace transformers including PubMedBERT
- tqdm - progress bars
- google-cloud-bigquery - BigQuery client
- google-cloud-storage - GCS client

All packages are verified after installation before proceeding.
