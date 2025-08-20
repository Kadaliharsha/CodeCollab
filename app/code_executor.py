import docker
from docker.errors import ContainerError
import time

def run_python_code(user_code, test_input):
    """
    Runs a string of Python code in a secure, isolated Docker container.
    
    Args:
        user_code (str): The user's Python code, expected to be a function definition.
        test_string (str): The input to pass to the user's function.
        
    Returns:
        A tuple containing (output, error), both as strings.
    """
    
    client = docker.from_env()
    image_name = "python:3.9-slim"
    
    # Command to run inside the container. We're telling it it execute our code string.
    # The '-c' flag tells python to execute the command that follows.
    client = docker.from_env()
    image_name = "python:3.9-slim"

    full_script = f"""
# --- User's Code ---    
{user_code}    

# --- Execution ---
# We call the 'solve' function with the provided input
try:
    result = solve({test_input})
    print(result)
except Exception as e:
    print(e)
"""
    command = ["python", "-c", full_script]
    container = None
    try:
        # 1. Create the container
        container = client.containers.create(
            image=image_name,
            command=command,
            network_disabled=True,
            mem_limit="256m",
            detach=True,
        )

        # 2. Start the container
        container.start()

        # 3. Wait for the container to finish and get the output
        container.wait(timeout=5)
        
        output = container.logs(stdout=True, stderr=False).decode('utf-8')
        error = container.logs(stdout=False, stderr=True).decode('utf-8')

        return output, error
    
    except ContainerError as e:
        # This catches errors if the code itself is invalid
        return "", str(e)
    
    except Exception as e:
        # This catches other errors
        return "", str(e)

    finally:
        # Clean up: Stop and remove the container
        if container:
            container.stop()
            container.remove()