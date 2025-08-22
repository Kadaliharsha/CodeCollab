import docker
import base64

def run_code(code, language, test_input=""):
    """
    Runs a string of code in a specific language in a secure Docker container
    using Base64 encoding to safely handle all characters.
    """
    client = docker.from_env()
    
    image_name = ""
    command = ""
    
    # Encode the user's code into a Base64 string
    encoded_code = base64.b64encode(code.encode('utf-8')).decode('utf-8')
    
    if language == 'python':
        image_name = "python:3.9-slim"
        # Decode the Base64 string and pipe it into the python interpreter
        command = f"/bin/sh -c \"echo {encoded_code} | base64 -d | python\""
    elif language == 'cpp':
        image_name = "gcc:latest"
        # Decode to a file, compile, then run
        command = f"/bin/sh -c \"echo {encoded_code} | base64 -d > main.cpp && g++ -o main main.cpp && ./main\""
    elif language == 'java':
        image_name = "openjdk:11-jdk-slim"
        # Decode to a file, compile, then run
        command = f"/bin/sh -c \"echo {encoded_code} | base64 -d > Main.java && javac Main.java && java Main\""
    else:
        return "", "Unsupported language"

    try:
        container = client.containers.run(
            image_name,
            command,
            detach=True,
            network_disabled=True,
            stdin_open=True,
        )
        
        # Send input to the container if provided
        if test_input:
            sock = container.attach_socket(params={'stdin': 1, 'stream': 1})
            sock._sock.sendall(test_input.encode('utf-8'))
            sock._sock.close()

        # Wait for the container to finish, with a generous timeout for image pulls
        result = container.wait(timeout=20)
        
        output = container.logs(stdout=True, stderr=False).decode('utf-8').strip()
        error = container.logs(stdout=False, stderr=True).decode('utf-8').strip()
        
        # Check the exit code from the container
        if result['StatusCode'] != 0 and not output:
             return "", error or "An unknown error occurred."

        return output, error

    except docker.errors.ImageNotFound:
        try:
            print(f"Pulling image: {image_name}. This may take a moment...")
            client.images.pull(image_name)
            print("Image pulled successfully. Please try running the code again.")
            return "", "Docker image was just pulled. Please run the code again."
        except Exception as pull_error:
            return "", f"Failed to pull Docker image: {pull_error}"
    except Exception as e:
        return "", str(e)
    finally:
        if 'container' in locals() and container:
            try:
                container.remove(force=True)
            except docker.errors.NotFound:
                pass