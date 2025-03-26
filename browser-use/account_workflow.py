#!/usr/bin/env python
import threading
import os
from dotenv import load_dotenv

# Import the workflow classes from each module
from reply_draft_workflow import TweetCreatorFlow as ReplyDraftFlow
from setup_new_account_workflow import TweetCreatorFlow as SetupAccountFlow
from tweet_finder_workflow import TweetCreatorFlow as TweetFinderFlow

load_dotenv()

def run_reply_draft_workflow():
    workflow = ReplyDraftFlow()
    workflow.kickoff()

def run_setup_account_workflow():
    workflow = SetupAccountFlow()
    workflow.kickoff()

def run_tweet_finder_workflow():
    workflow = TweetFinderFlow()
    workflow.kickoff()

def main():
    # Create threads for each workflow
    reply_thread = threading.Thread(target=run_reply_draft_workflow)
    setup_thread = threading.Thread(target=run_setup_account_workflow)
    finder_thread = threading.Thread(target=run_tweet_finder_workflow)

    # Start all threads
    reply_thread.start()
    setup_thread.start()
    finder_thread.start()

    # Wait for all threads to complete
    reply_thread.join()
    setup_thread.join()
    finder_thread.join()

if __name__ == "__main__":
    main()