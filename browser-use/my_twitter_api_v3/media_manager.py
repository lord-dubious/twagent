#!/usr/bin/env python3
"""
Media Manager for Twitter Automation

This module handles media management for Twitter automation, including:
- Automatic selection of media files from a directory
- LLM-based captioning of media files
- Media type detection and validation
"""

import os
import random
from typing import Dict, List, Any, Optional, Tuple, Union
import glob
from pathlib import Path
import mimetypes

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage


class MediaManager:
    """
    Manages media files for Twitter automation.
    
    This class handles automatic selection of media files from a directory,
    LLM-based captioning of media files, and media type detection and validation.
    """

    def __init__(self, 
                 media_dir: Optional[str] = None,
                 llm_model: str = "gpt-4o"):
        """
        Initialize the media manager.
        
        Args:
            media_dir: Path to the media directory (optional)
            llm_model: LLM model to use for captioning
        """
        self.media_dir = media_dir or os.path.join(os.getcwd(), "media")
        self.llm = ChatOpenAI(model=llm_model, temperature=0.7)
        
        # Ensure media directory exists
        os.makedirs(self.media_dir, exist_ok=True)
        
        # Initialize mimetypes
        mimetypes.init()
    
    def get_random_media(self, 
                        media_type: Optional[str] = None, 
                        persona_context: Optional[Dict[str, Any]] = None,
                        max_images: int = 4,
                        single_image_probability: float = 0.9) -> Union[List[str], str, None]:
        """
        Get random media file(s) from the media directory following Twitter guidelines.
        
        Args:
            media_type: Type of media to select (image, video, gif, or None for any)
            persona_context: Persona context for filtering media (optional)
            max_images: Maximum number of images to return (Twitter allows up to 4)
            single_image_probability: Probability of returning just 1 image (0.0-1.0)
            
        Returns:
            Path(s) to the selected media file(s), or None if no suitable media found.
            Returns a string for single file, list for multiple files.
        """
        # Define file extensions for each media type
        extensions = {
            "image": [".jpg", ".jpeg", ".png"],
            "video": [".mp4", ".mov", ".avi"],
            "gif": [".gif"]
        }
        
        # Get all media files in the directory
        all_files = []
        
        if media_type and media_type in extensions:
            # Get files of the specified type
            for ext in extensions[media_type]:
                all_files.extend(glob.glob(os.path.join(self.media_dir, f"*{ext}")))
        else:
            # Get all media files
            for media_exts in extensions.values():
                for ext in media_exts:
                    all_files.extend(glob.glob(os.path.join(self.media_dir, f"*{ext}")))
        
        # Filter files based on persona context if provided
        filtered_files = all_files
        if persona_context:
            # TODO: Implement more sophisticated filtering based on persona context
            # For now, just use basic keyword matching
            topics = persona_context.get("topics", [])
            if topics:
                topic_keywords = [topic.lower().split()[0] for topic in topics]
                filtered_files = [
                    f for f in all_files 
                    if any(keyword in os.path.basename(f).lower() for keyword in topic_keywords)
                ]
                
                # If no files match the topics, fall back to all files
                if not filtered_files:
                    filtered_files = all_files
        
        # Return None if no files found
        if not filtered_files:
            return None
        
        # Separate files by type
        image_files = [f for f in filtered_files if any(f.lower().endswith(ext) for ext in extensions["image"])]
        video_files = [f for f in filtered_files if any(f.lower().endswith(ext) for ext in extensions["video"])]
        gif_files = [f for f in filtered_files if any(f.lower().endswith(ext) for ext in extensions["gif"])]
        
        # Twitter rules:
        # - Can include up to 4 images OR 1 GIF OR 1 video
        # - Cannot mix media types
        
        # Decide which type of media to use based on availability
        if media_type == "video" and video_files:
            # For video, always return a single file
            return random.choice(video_files)
        elif media_type == "gif" and gif_files:
            # For GIF, always return a single file
            return random.choice(gif_files)
        elif media_type == "image" and image_files:
            # For images, decide how many to return (1-4)
            return self._select_images(image_files, max_images, single_image_probability)
        elif not media_type:
            # If no specific type requested, prioritize based on availability
            if video_files:
                return random.choice(video_files)
            elif gif_files:
                return random.choice(gif_files)
            elif image_files:
                return self._select_images(image_files, max_images, single_image_probability)
        
        # If we get here, no suitable media was found
        return None
    
    def _select_images(self, 
                      image_files: List[str], 
                      max_images: int = 4, 
                      single_image_probability: float = 0.9) -> Union[List[str], str]:
        """
        Select random images following Twitter guidelines.
        
        Args:
            image_files: List of image file paths
            max_images: Maximum number of images to return (Twitter allows up to 4)
            single_image_probability: Probability of returning just 1 image (0.0-1.0)
            
        Returns:
            Path(s) to the selected image(s). String for single image, list for multiple.
        """
        # Ensure max_images is within Twitter's limits
        max_images = min(max_images, 4)
        
        # Determine if we should return a single image based on probability
        use_single_image = random.random() < single_image_probability
        
        if use_single_image or len(image_files) == 1 or max_images == 1:
            # Return a single image
            return random.choice(image_files)
        else:
            # Determine how many images to return (2-4, limited by available files)
            num_images = min(random.randint(2, max_images), len(image_files))
            
            # Return multiple images
            return random.sample(image_files, num_images)
    
    def get_media_type(self, file_path: str) -> Optional[str]:
        """
        Get the type of a media file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Type of the media file (image, video, gif), or None if unknown
        """
        if not os.path.exists(file_path):
            return None
        
        # Get the file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Check the file extension
        if ext in [".jpg", ".jpeg", ".png"]:
            return "image"
        elif ext in [".mp4", ".mov", ".avi"]:
            return "video"
        elif ext == ".gif":
            return "gif"
        
        # If extension doesn't match, try using mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type:
            if mime_type.startswith("image"):
                return "image"
            elif mime_type.startswith("video"):
                return "video"
        
        return None
    
    async def generate_caption(self, 
                              file_path: str, 
                              persona_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a caption for a media file using LLM.
        
        Args:
            file_path: Path to the media file
            persona_context: Persona context for caption generation (optional)
            
        Returns:
            Generated caption
        """
        if not os.path.exists(file_path):
            return "Media file not found"
        
        # Get the media type
        media_type = self.get_media_type(file_path)
        if not media_type:
            return "Unknown media type"
        
        # Get the file name (might contain descriptive information)
        file_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(file_name)[0]
        
        # Replace underscores and hyphens with spaces for better readability
        file_name_readable = file_name_without_ext.replace("_", " ").replace("-", " ")
        
        # Build the prompt
        if persona_context:
            # If persona context is provided, generate a persona-specific caption
            agent_name = persona_context.get("agent_name", "")
            system_prompt = persona_context.get("system", "")
            topics = persona_context.get("topics", [])
            adjectives = persona_context.get("adjectives", [])
            
            # Select a random topic and adjective if available
            topic = random.choice(topics) if topics else ""
            adjective = random.choice(adjectives) if adjectives else ""
            
            prompt = f"""You are helping {agent_name} create a caption for a {media_type} they are posting on social media.

About {agent_name}:
{system_prompt}

The {media_type} file name is: {file_name_readable}

Create a brief, engaging caption that:
1. Describes what might be in this {media_type} based on the file name
2. Relates to the topic of "{topic}" if possible
3. Has a {adjective} tone
4. Sounds natural and authentic to {agent_name}'s voice
5. Is 1-2 sentences long

Do not use hashtags or emojis. The caption should be conversational and personal.
"""
        else:
            # If no persona context, generate a generic caption
            prompt = f"""Create a brief, engaging caption for a {media_type} with the file name: {file_name_readable}

The caption should:
1. Describe what might be in this {media_type} based on the file name
2. Be conversational and personal
3. Be 1-2 sentences long

Do not use hashtags or emojis.
"""
        
        # Generate caption
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Clean up the caption
        caption = response.content.strip()
        
        # Remove quotes if present
        if caption.startswith('"') and caption.endswith('"'):
            caption = caption[1:-1]
        
        return caption


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create media manager
        manager = MediaManager()
        
        # Get a random media file
        media_file = manager.get_random_media()
        
        if media_file:
            print(f"Selected media file: {media_file}")
            
            # Get the media type
            media_type = manager.get_media_type(media_file)
            print(f"Media type: {media_type}")
            
            # Generate a caption
            caption = await manager.generate_caption(media_file)
            print(f"Generated caption: {caption}")
        else:
            print("No media files found")
    
    asyncio.run(main())
