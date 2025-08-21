import docker

def run_code(code, language, test_input=""):
    """
    Runs a string of code in a specific language in a secure Docker container.
    """
    client = docker.from_env()
    
    image_name = ""
    command = ""
    
    if language == 'python':
        image_name = "python:3.9-slim"
        # Command to execute the code string directly
        command = f"python -c \"{code.replace('\"', '\\\"')}\""
    elif language == 'cpp':
        image_name = "gcc:latest"
        # Using triple quotes ''' to simplify the command string and avoid syntax errors
        # This correctly handles escaping single quotes in the user's code for the shell.
        safe_code = code.replace("'", "'\\''")
        command = f'''/bin/sh -c "echo '{safe_code}' > main.cpp && g++ -o main main.cpp && ./main"'''
    elif language == 'java':
        image_name = "openjdk:11-jre-slim"
        # Using triple quotes ''' here as well for the same reason.
        safe_code = code.replace("'", "'\\''")
        command = f'''/bin/sh -c "echo '{safe_code}' > Main.java && javac Main.java && java Main"'''
    else:
        return "", "Unsupported language"

    container = None
    try:
        # Use client.containers.run() which is simpler for one-off tasks
        container_output = client.containers.run(
            image_name,
            command,
            detach=False, # Wait for the container to finish
            remove=True,  # Automatically remove it after it's done
            network_disabled=True,
        )
        # The output is returned directly as bytes
        output = container_output.decode('utf-8').strip()
        return output, "" # Return output and an empty error string

    except docker.errors.ContainerError as e:
        # This error happens if the code inside the container fails (e.g., runtime error)
        # The error message is in the container's output
        error_message = e.stderr.decode('utf-8').strip()
        return "", error_message
    except docker.errors.ImageNotFound:
        # If the image isn't downloaded yet, instruct the user
        try:
            print(f"Pulling image: {image_name}. This may take a moment...")
            client.images.pull(image_name)
            print("Image pulled successfully. Please try running the code again.")
            return "", "Docker image was just pulled. Please run the code again."
        except Exception as pull_error:
            return "", f"Failed to pull Docker image: {pull_error}"
    except Exception as e:
        # Catch any other unexpected errors
        return "", str(e)

