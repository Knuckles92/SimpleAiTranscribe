import logging
import whisper
import os
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.text import Text
import time

console = Console()

class Transcriber:
    def __init__(self, model_choice):
        self.model_choice = model_choice
        self.use_api = model_choice.startswith('api_')
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.should_cancel = False

        if not self.api_key:
            try:
                from dotenv import load_dotenv
                env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
                load_dotenv(env_path)
                self.api_key = os.getenv('OPENAI_API_KEY')
            except ImportError:
                logging.warning("python-dotenv not installed. Skipping .env file loading.")
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")

        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

        if not self.use_api:
            logging.info("Loading Whisper model...")
            self.model = whisper.load_model("base")
            logging.info("Model loaded!")
        else:
            self.model = None

    def transcribe(self, audio_file_path, progress_callback=None):
        """
        Transcribe audio file using either local Whisper model or OpenAI API
        
        Args:
            audio_file_path: Path to the audio file
            progress_callback: Optional callback function to report progress
            
        Returns:
            Transcribed text
        """
        try:
            if self.should_cancel:
                return None

            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[bold]{task.percentage:.0f}%"),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                transcribe_task = progress.add_task("[cyan]Transcribing audio...", total=100)
                progress.update(transcribe_task, advance=10)
                
                if self.use_api:
                    if self.model_choice == "api_whisper":
                        api_model = "whisper-1"
                    elif self.model_choice == "api_gpt4o":
                        api_model = "gpt-4o-transcribe"
                    elif self.model_choice == "api_gpt4o_mini":
                        api_model = "gpt-4o-mini-transcribe"

                    logging.info("\n=== Using OpenAI API ===")
                    if not self.api_key:
                        logging.error("Error: No API key found!")
                        raise ValueError("OpenAI API key not found in environment variables (OPENAI_API_KEY)")

                    logging.info(f"Using model: {self.model_choice}")
                    logging.info(f"Selected API model: {api_model}")
                    logging.info("Sending audio file to OpenAI API...")
                    progress.update(transcribe_task, description="[magenta]Sending to OpenAI API...", advance=20)

                    with open(audio_file_path, "rb") as audio_file:
                        response = self.client.audio.transcriptions.create(
                            model=api_model,
                            file=audio_file,
                            response_format="text"
                        )
                    transcribed_text = response.strip()
                    logging.info(f"API Response received. Length: {len(transcribed_text)} characters")
                    progress.update(transcribe_task, description="[green]Processing API response...", advance=60)
                else:
                    logging.info("\n=== Using Local Whisper Model ===")
                    logging.info("Processing audio with local model...")
                    progress.update(transcribe_task, description="[magenta]Processing with local Whisper model...", advance=20)
                    result = self.model.transcribe(audio_file_path)
                    transcribed_text = result['text'].strip()
                    logging.info(f"Local transcription complete. Length: {len(transcribed_text)} characters")
                    progress.update(transcribe_task, description="[green]Finalizing transcription...", advance=60)

                    if self.should_cancel:
                        logging.info("Transcription cancelled by user")
                        return None

                logging.info(f"Final transcription: {transcribed_text}")
                
                if 'progress' in locals():
                    progress.update(transcribe_task, description="[bold green]Transcription complete!", advance=10)
                
                console.print(Panel(
                    Text(transcribed_text, style="white"),
                    title="[bold green]Transcription Result[/bold green]",
                    border_style="green",
                    expand=True
                ))
                
                return transcribed_text

        except Exception as e:
            logging.error(f"\nError during transcription: {str(e)}")
            console.print(Panel(
                Text(f"Error: {str(e)}", style="bold red"),
                title="[bold red]Transcription Failed[/bold red]",
                border_style="red",
                expand=False
            ))
            return None

    def cancel(self):
        """Cancel an ongoing transcription"""
        self.should_cancel = True
