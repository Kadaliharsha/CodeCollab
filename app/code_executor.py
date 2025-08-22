import docker
import base64

def run_code(user_code, language, test_input_args=""):
    """
    Runs code in a secure Docker container using Base64 encoding to prevent
    syntax errors with complex code strings.
    """
    client = docker.from_env()
    
    image_name = ""
    command = ""
    
    # We build a full script to execute inside the container.
    if test_input_args:
        # This logic is for the "Submit" button (judging test cases)
        full_script = f"""
# User's function definition
{user_code}

# Call the function with the specific test case arguments and print the result
try:
    result = solve({test_input_args})
    print(result)
except Exception as e:
    import sys
    print(e, file=sys.stderr)
"""
    else:
        # This logic is for the "Run" button (simple execution)
        full_script = user_code

    # We encode the full script to Base64 to safely pass it to the container
    encoded_script = base64.b64encode(full_script.encode('utf-8')).decode('utf-8')

    if language == 'python':
        image_name = "python:3.9-slim"
        # Decode the Base64 string and pipe it into the python interpreter
        command = f"/bin/sh -c \"echo {encoded_script} | base64 -d | python\""
    elif language == 'cpp':
        image_name = "gcc:latest"
        # Decode to a file, compile, then run
        command = f"/bin/sh -c \"echo {encoded_script} | base64 -d > main.cpp && g++ -o main main.cpp && ./main\""
    elif language == 'java':
        image_name = "openjdk:11-jdk-slim"
        # Decode to a file, compile, then run
        command = f"/bin/sh -c \"echo {encoded_script} | base64 -d > Main.java && javac Main.java && java Main\""
    else:
        return "", "Unsupported language"

    try:
        container = client.containers.run(
            image_name,
            command,
            detach=False,
            remove=True,
            network_disabled=True,
        )
        output = container.decode('utf-8').strip()
        return output, ""

    except docker.errors.ContainerError as e:
        error_message = e.stderr.decode('utf-8').strip()
        return "", error_message
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