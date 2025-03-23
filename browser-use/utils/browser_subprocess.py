import json
import os
import subprocess
import tempfile
from typing import Optional

def call_twitter_reply_script(reply_text: str, original_tweet_url: Optional[str] = None) -> None:
    """
    Call the Twitter reply script in the browser-use environment
    
    Args:
        reply_text: The text of the reply tweet
        original_tweet_url: URL of the original tweet to reply to (optional)
    """
    # Create a temporary file to pass the data between environments
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        json.dump({
            "tweet_text": reply_text,
            "tweet_url": original_tweet_url
        }, tmp)
        temp_file_path = tmp.name
    
    try:
        # Get the path relative to the current file's location
        # Since we've moved from main.py to utils/browser_subprocess.py, 
        # we need to adjust our path calculations
        current_dir = os.path.dirname(os.path.abspath(__file__))  # Gets guide_creator_flow/utils/
        agents_src_dir = os.path.dirname(os.path.dirname(current_dir))  # Goes up two levels to src/
        agents_dir = os.path.dirname(agents_src_dir)  # Goes up one more level to agents/
        project_root = os.path.dirname(agents_dir)  # Goes up one more level to get the root
        
        reply_script_path = os.path.join(
            project_root, 
            "browser-use", 
            "my_twitter_api_v3", 
            "manage_posts", 
            "reply_to_post.py"
        )
        
        # Check if the script exists
        if not os.path.exists(reply_script_path):
            # Try alternative path - browser-use/twitter/...
            reply_script_path = os.path.join(
                project_root, 
                "browser-use", 
                "my_twitter_api_v3", 
                "manage_posts", 
                "reply_to_post.py"
            )
            
            if not os.path.exists(reply_script_path):
                print(f"Error: Could not find Twitter reply script at expected locations.")
                print(f"Tried: {os.path.join(project_root, 'browser-use', 'my_twitter_api_v3', 'manage_posts', 'reply_to_post.py')}")
                print(f"Tried: {reply_script_path}")
                print(f"Project root is: {project_root}")
                return
        
        print(f"Calling Twitter reply script: {reply_script_path}")
        print("This will run in a separate process. Please check the browser-use logs for details.")
        
        # Run the script directly without changing environments
        cmd = f'python "{reply_script_path}" --data "{temp_file_path}"'
        subprocess.Popen(cmd, shell=True)
    except Exception as e:
        print(f"Error calling Twitter reply script: {str(e)}")
    finally:
        # Note: Temp file will need to be cleaned up by the reply script
        pass