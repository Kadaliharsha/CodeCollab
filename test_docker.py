import docker

def run_test():
    """
    A simple script to test the connection to the Docker daemon
    and run a basic command.
    """
    print("Attempting to connect to Docker...")
    try:
        client = docker.from_env()
        print("Successfully connected to Docker!")
    except Exception as e:
        print("\n--- ERROR ---")
        print("Failed to connect to Docker. Please ensure Docker Desktop is running.")
        print(f"Error details: {e}")
        return

    image_name = "python:3.9-slim"
    command = ["python", "-c", "print('Hello from Docker!')"]
    
    print(f"\nAttempting to run a container with image: {image_name}...")
    container = None
    try:
        container = client.containers.run(
            image_name,
            command,
            detach=False, # Run and wait for it to finish
            remove=True,   # Automatically remove the container when done
        )
        # The output of the container is returned directly
        output = container.decode('utf-8').strip()
        print("\n--- SUCCESS ---")
        print(f"Container ran successfully. Output: {output}")

    except docker.errors.ImageNotFound:
        print("\n--- INFO ---")
        print(f"Docker image '{image_name}' not found locally.")
        print("Docker will now pull the image. This might take a few minutes...")
        try:
            client.images.pull(image_name)
            print("Image pulled successfully! Please run the script again.")
        except Exception as e:
            print("\n--- ERROR ---")
            print(f"Failed to pull the Docker image. Error details: {e}")
            
    except Exception as e:
        print("\n--- ERROR ---")
        print("An error occurred while trying to run the container.")
        print(f"Error details: {e}")

if __name__ == '__main__':
    run_test()
