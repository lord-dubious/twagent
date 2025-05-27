# Persona-Based Tweet Generation

This module enables persona-based tweet generation for Twitter automation, including support for media tweets and persona-based interactions.

## Features

- **Persona Integration**: Create tweets in the voice and style of a specific persona
- **Media Support**: Generate tweets that reference included media
- **Content Generation**: Create posts, replies, and quote tweets
- **Timeline Monitoring**: Automatically monitor timeline and interact with relevant content
- **Decision Making**: Decide what action to take on tweets based on persona preferences
- **Automatic Content Selection**: Automatically selects topics and adjectives from persona data
- **Automatic Media Selection**: Randomly selects media files from a directory and generates captions

## Persona Configuration

Personas are defined in JSON files with the following structure:

```json
{
  "name": "Persona Name",
  "twitter_username": "TwitterHandle",
  "system": "System prompt describing the persona",
  "bio": ["Bio line 1", "Bio line 2"],
  "lore": ["Background detail 1", "Background detail 2"],
  "messageExamples": [...],
  "postExamples": [...],
  "adjectives": ["Adjective1", "Adjective2"],
  "topics": ["Topic1", "Topic2"],
  "style": {
    "all": ["Style guideline 1", "Style guideline 2"],
    "chat": ["Chat guideline 1", "Chat guideline 2"],
    "post": ["Post guideline 1", "Post guideline 2"]
  }
}
```

See `personas/holly_snow.json` for a complete example.

## Usage

### Command Line

#### Generate a Post

```bash
# Generate a post with a specific persona
python persona_tweet_example.py --persona personas/holly_snow.json --action post

# Generate a post with specific media
python persona_tweet_example.py --persona personas/holly_snow.json --action post --media path/to/image.jpg

# Generate a post with random media from the media directory
python persona_tweet_example.py --persona personas/holly_snow.json --action post --random-media
```

#### Generate a Reply

```bash
# Generate a reply to a tweet
python persona_tweet_example.py --persona personas/holly_snow.json --action reply --tweet "Just finished my workout! Feeling great!"

# Generate a reply with random media
python persona_tweet_example.py --persona personas/holly_snow.json --action reply --tweet "Just finished my workout! Feeling great!" --random-media
```

#### Decide Action

```bash
# Decide what action to take on a tweet
python persona_tweet_example.py --persona personas/holly_snow.json --action decide --tweet "Check out my new fitness routine! It's perfect for beginners."
```

### Automated Workflow

```bash
# Post a tweet with persona integration
python -m browser_use.my_twitter_api_v3.persona_tweet_workflow --persona personas/holly_snow.json --action post

# Post a tweet with random media
python -m browser_use.my_twitter_api_v3.persona_tweet_workflow --persona personas/holly_snow.json --action post --random-media

# Run timeline monitoring with random media
python -m browser_use.my_twitter_api_v3.persona_tweet_workflow --persona personas/holly_snow.json --action monitor --interval 1800 --max-posts 10 --random-media
```

## Components

### PersonaManager

The `PersonaManager` class handles loading and parsing persona data from JSON files, and generating prompts for LLM-based content creation.

```python
from browser_use.my_twitter_api_v3.persona_manager import PersonaManager

# Create persona manager
manager = PersonaManager("personas/holly_snow.json")

# Generate a post prompt
post_prompt = manager.generate_post_prompt(
    topic="Fitness & Workouts",
    adjective="Seductive",
    media_description="A photo of a sunset at the beach"
)
```

### MediaManager

The `MediaManager` class handles automatic selection of media files and LLM-based captioning.

```python
from browser_use.my_twitter_api_v3.media_manager import MediaManager

# Create media manager
manager = MediaManager(media_dir="media")

# Get random media file
media_file = manager.get_random_media()

# Generate caption
caption = await manager.generate_caption(media_file)
```

### TweetGenerator

The `TweetGenerator` class handles LLM-based content creation with persona integration, supporting posts, replies, and quote tweets.

```python
from browser_use.my_twitter_api_v3.tweet_generator import TweetGenerator

# Create tweet generator
generator = TweetGenerator(persona_file_path="personas/holly_snow.json")

# Generate a post - topics and adjectives are automatically selected
post = await generator.generate_post(
    media_description="A photo of a sunset at the beach"
)
```

### PersonaTweetWorkflow

The `PersonaTweetWorkflow` class handles the workflow for posting tweets with persona integration, including timeline monitoring and automated interactions.

```python
from browser_use.my_twitter_api_v3.persona_tweet_workflow import PersonaTweetWorkflow

# Create workflow
workflow = PersonaTweetWorkflow(persona_file_path="personas/holly_snow.json")

# Create post with random media
success = await workflow.create_persona_post(
    use_random_media=True
)

# Run timeline monitoring with random media
await workflow.run_timeline_monitoring(
    interval=3600,
    max_posts=5,
    use_random_media=True
)
```

## Media Directory Structure

The media directory should contain image, video, and GIF files that the system can randomly select for posts. For best results:

1. Name files descriptively (e.g., `beach_sunset.jpg`, `workout_selfie.jpg`)
2. Organize files by topic if desired (the system will try to match topics from the persona)
3. Use common formats:
   - Images: `.jpg`, `.jpeg`, `.png`
   - Videos: `.mp4`, `.mov`, `.avi`
   - GIFs: `.gif`

## Creating New Personas

To create a new persona:

1. Create a new JSON file in the `personas` directory
2. Follow the structure in `personas/holly_snow.json`
3. Include:
   - Basic information (name, username, system prompt)
   - Bio and background details
   - Message and post examples
   - Adjectives and topics
   - Style guidelines

## Best Practices

- **Persona Consistency**: Ensure the persona's voice and style are consistent across all content
- **Media Integration**: Provide a variety of media files that match the persona's interests and topics
- **Topic Selection**: Include a variety of topics in the persona data for diverse content generation
- **Style Guidelines**: Include detailed style guidelines to help the LLM generate appropriate content
- **Examples**: Provide plenty of examples to help the LLM understand the persona's voice and style
