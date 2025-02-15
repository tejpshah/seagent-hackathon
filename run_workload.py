import subprocess

def run_command(command):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Command failed with return code {result.returncode}")
    else:
        print("Command completed successfully.\n")

def main():
    # Run batch workload using the batch config file
    run_command("python main.py --config config_batch.yaml --strategy batch")
    
    # Run threaded workload using the threaded config file
    run_command("python main.py --config config_threaded.yaml --strategy threaded")

if __name__ == "__main__":
    main()
