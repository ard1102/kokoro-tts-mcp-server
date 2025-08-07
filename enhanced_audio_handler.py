#!/usr/bin/env python3
"""
Pure Python, Cross-Platform Audio Handler for Kokoro TTS MCP Server

This module provides a comprehensive, pure Python solution for audio playback
that works across different platforms (Windows, macOS, Linux) with multiple
audio library fallbacks and Windows-specific optimizations.
"""

import os
import sys
import json
import time
import threading
import platform
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import subprocess
import ctypes
from ctypes import wintypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_handler")

class PurePythonAudioHandler:
    """Pure Python, cross-platform audio handler with Windows optimizations"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Platform detection
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        
        # Detect available audio libraries
        self._audio_libraries = self._detect_available_libraries()
        
        # Windows-specific audio device detection
        self._windows_audio_devices = {}
        if self.is_windows:
            self._windows_audio_devices = self._detect_windows_audio_devices()
        
        logger.info(f"🎵 Audio Handler initialized for {platform.system()}")
        logger.info(f"📁 Output directory: {self.output_dir.absolute()}")
        logger.info(f"🔊 Available libraries: {[k for k, v in self._audio_libraries.items() if v]}")
    
    def get_available_libraries(self):
        """Get information about available audio libraries"""
        return self._audio_libraries.copy()
    
    def _detect_windows_audio_devices(self) -> Dict[str, Any]:
        """Detect Windows audio devices and capabilities"""
        devices_info = {
            "winsound_available": False,
            "mci_available": False,
            "audio_drivers": [],
            "default_device": None
        }
        
        try:
            # Check if winsound is available (built-in Windows module)
            import winsound
            devices_info["winsound_available"] = True
            logger.info("✅ Windows winsound module available")
        except ImportError:
            logger.warning("⚠️ Windows winsound module not available")
        
        try:
            # Check Windows audio drivers
            drivers_info = self._check_windows_audio_drivers()
            devices_info.update(drivers_info)
        except Exception as e:
            logger.warning(f"⚠️ Could not detect Windows audio drivers: {e}")
        
        return devices_info
    
    def _detect_available_libraries(self) -> Dict[str, bool]:
        """Detect which audio libraries are available"""
        libraries = {
            "pygame": False,
            "sounddevice": False,
            "pydub": False,
            "simpleaudio": False,
            "scipy": False  # Required for sounddevice WAV loading
        }
        
        # Test pygame
        try:
            import pygame
            libraries["pygame"] = True
            logger.info("✅ pygame available")
        except ImportError:
            logger.info("ℹ️ pygame not available")
        
        # Test sounddevice
        try:
            import sounddevice as sd
            libraries["sounddevice"] = True
            logger.info("✅ sounddevice available")
            
            # Check for scipy (required for WAV file loading)
            try:
                import scipy.io.wavfile
                libraries["scipy"] = True
                logger.info("✅ scipy available (required for sounddevice WAV loading)")
            except ImportError:
                logger.warning("⚠️ scipy not available - sounddevice will have limited functionality")
                
        except ImportError:
            logger.info("ℹ️ sounddevice not available")
        
        # Test pydub
        try:
            from pydub import AudioSegment
            libraries["pydub"] = True
            logger.info("✅ pydub available")
        except ImportError:
            logger.info("ℹ️ pydub not available")
        
        # Test simpleaudio
        try:
            import simpleaudio as sa
            libraries["simpleaudio"] = True
            logger.info("✅ simpleaudio available")
        except ImportError:
            logger.info("ℹ️ simpleaudio not available")
        
        # Log summary
        available_count = sum(libraries.values())
        if available_count == 0:
            logger.warning("⚠️ No audio libraries detected! Audio playback will not work.")
            logger.info("💡 Install audio libraries: pip install pygame sounddevice pydub simpleaudio scipy")
        else:
            logger.info(f"🎵 {available_count} audio libraries available")
        
        return libraries
    
    def _check_windows_audio_drivers(self) -> Dict[str, Any]:
        """Check Windows audio drivers and services"""
        driver_info = {
            "audio_service_running": False,
            "audio_drivers": [],
            "mci_available": False
        }
        
        try:
            # Check if Windows Audio service is running
            result = subprocess.run(
                ['sc', 'query', 'AudioSrv'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if "RUNNING" in result.stdout:
                driver_info["audio_service_running"] = True
                logger.info("✅ Windows Audio service is running")
            else:
                logger.warning("⚠️ Windows Audio service may not be running")
        except Exception as e:
            logger.warning(f"⚠️ Could not check Windows Audio service: {e}")
        
        try:
            # Check for MCI (Media Control Interface) availability
            import ctypes
            winmm = ctypes.windll.winmm
            if winmm:
                driver_info["mci_available"] = True
                logger.info("✅ Windows MCI (Media Control Interface) available")
        except Exception as e:
            logger.warning(f"⚠️ Windows MCI not available: {e}")
        
        return driver_info
    
    def _verify_audio_format(self, file_path: Path) -> Dict[str, Any]:
        """Verify audio file format and provide recommendations"""
        try:
            suffix = file_path.suffix.lower()
            
            format_info = {
                "format": suffix,
                "supported": True,
                "recommendations": []
            }
            
            # Check format compatibility
            if suffix == ".wav":
                format_info["recommendations"].append("WAV format - excellent compatibility")
            elif suffix == ".mp3":
                format_info["recommendations"].append("MP3 format - good compatibility, may need pydub")
            elif suffix in [".ogg", ".flac", ".m4a", ".aac"]:
                format_info["recommendations"].append(f"{suffix.upper()} format - may need pydub for playback")
            else:
                format_info["supported"] = False
                format_info["recommendations"].append(f"Unknown format {suffix} - convert to WAV for best compatibility")
            
            # Check file size
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > 50:
                format_info["recommendations"].append(f"Large file ({size_mb:.1f}MB) - may take time to load")
            
            return format_info
            
        except Exception as e:
            return {
                "format": "unknown",
                "supported": False,
                "error": str(e),
                "recommendations": ["Could not analyze file format"]
            }
    
    def _handle_windows_mci_error(self, error_msg: str) -> Dict[str, Any]:
        """Handle Windows MCI (Media Control Interface) errors"""
        mci_errors = {
            "263": {
                "description": "The specified device is not open or is not recognized by MCI",
                "solutions": [
                    "Restart Windows Audio service",
                    "Update audio drivers",
                    "Try running as administrator",
                    "Convert audio file to WAV format"
                ]
            },
            "device": {
                "description": "Audio device not available or in use",
                "solutions": [
                    "Close other audio applications",
                    "Check if audio device is connected",
                    "Restart audio service",
                    "Try a different audio format"
                ]
            },
            "default": {
                "description": "General MCI audio error",
                "solutions": [
                    "Restart Windows Audio service: services.msc -> Windows Audio -> Restart",
                    "Update Windows and audio drivers",
                    "Try converting file to WAV format",
                    "Run application as administrator"
                ]
            }
        }
        
        # Find matching error type
        for error_key, error_info in mci_errors.items():
            if error_key in error_msg.lower():
                return error_info
        
        return mci_errors["default"]
    
    def _windows_winsound_fallback(self, file_path: Path) -> Dict[str, Any]:
        """Windows winsound fallback for emergency audio playback"""
        try:
            import winsound
            
            # Only works with WAV files
            if file_path.suffix.lower() != ".wav":
                return {
                    "success": False,
                    "error": "winsound only supports WAV files",
                    "recommendation": "Convert file to WAV format"
                }
            
            # Play the WAV file
            winsound.PlaySound(str(file_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            
            logger.info(f"🆘 Emergency winsound playback started: {file_path.name}")
            return {
                "success": True,
                "message": f"Emergency playback with winsound: {file_path.name}",
                "method": "winsound",
                "file_path": str(file_path.absolute()),
                "note": "Emergency fallback - limited functionality"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def play_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Play an audio file using the best available method"""
        try:
            file_path = Path(file_path)
            
            # Verify file exists
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"Audio file not found: {file_path}",
                    "file_path": str(file_path)
                }
            
            # Verify audio format
            format_info = self._verify_audio_format(file_path)
            if not format_info["supported"]:
                logger.warning(f"⚠️ Unsupported audio format: {format_info}")
            
            logger.info(f"🎵 Attempting to play: {file_path.name}")
            
            # Method 1: sounddevice (best quality and cross-platform support)
            if self._audio_libraries.get('sounddevice', False) and self._audio_libraries.get('scipy', False):
                try:
                    import sounddevice as sd
                    import scipy.io.wavfile as wavfile
                    import numpy as np
                    
                    # Load audio file
                    sample_rate, audio_data = wavfile.read(str(file_path))
                    
                    # Handle different audio formats
                    if len(audio_data.shape) == 1:
                        # Mono audio
                        audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max
                    else:
                        # Stereo audio
                        if audio_data.dtype == np.int16:
                            audio_data = audio_data.astype(np.float32) / 32768.0
                        else:
                            audio_data = audio_data.astype(np.float32)
                    
                    # Play audio in a separate thread
                    def sounddevice_play():
                        try:
                            sd.play(audio_data, sample_rate)
                            sd.wait()  # Wait until playback is finished
                            logger.info(f"✅ sounddevice playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ sounddevice playback error: {e}")
                    
                    thread = threading.Thread(target=sounddevice_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ sounddevice playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with sounddevice: {file_path.name}",
                        "method": "sounddevice",
                        "file_path": str(file_path.absolute()),
                        "sample_rate": int(sample_rate),
                        "duration_seconds": len(audio_data) / sample_rate
                    }
                    
                except ImportError:
                    logger.warning("⚠️ scipy not available for sounddevice, trying next method")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ sounddevice error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg or "device" in error_msg.lower()):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows MCI issue detected: {mci_info['description']}")
                        logger.info(f"💡 Suggested solutions: {mci_info['solutions']}")
            
            # Method 2: pygame (reliable and cross-platform)
            if self._audio_libraries.get('pygame', False):
                try:
                    import pygame
                    
                    # Initialize pygame mixer if not already done
                    if not pygame.mixer.get_init():
                        pygame.mixer.pre_init(
                            frequency=44100,
                            size=-16,
                            channels=2,
                            buffer=1024
                        )
                        pygame.mixer.init()
                    
                    def pygame_play():
                        try:
                            pygame.mixer.music.load(str(file_path))
                            pygame.mixer.music.set_volume(1.0)
                            pygame.mixer.music.play()
                            
                            # Wait for playback to complete
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)
                            
                            logger.info(f"✅ pygame playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ pygame playback error: {e}")
                    
                    thread = threading.Thread(target=pygame_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ pygame playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with pygame: {file_path.name}",
                        "method": "pygame",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ pygame error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg or "mixer" in error_msg.lower()):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows audio issue detected: {mci_info['description']}")
            
            # Method 3: simpleaudio (lightweight and reliable)
            if self._audio_libraries.get('simpleaudio', False):
                try:
                    import simpleaudio as sa
                    
                    def simpleaudio_play():
                        try:
                            wave_obj = sa.WaveObject.from_wave_file(str(file_path))
                            play_obj = wave_obj.play()
                            play_obj.wait_done()  # Wait until playback is finished
                            logger.info(f"✅ simpleaudio playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ simpleaudio playback error: {e}")
                    
                    thread = threading.Thread(target=simpleaudio_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ simpleaudio playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with simpleaudio: {file_path.name}",
                        "method": "simpleaudio",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    logger.error(f"❌ simpleaudio error: {e}")
            
            # Method 4: pydub (with fallback playback)
            if self._audio_libraries.get('pydub', False):
                try:
                    from pydub import AudioSegment
                    from pydub.playback import play
                    
                    def pydub_play():
                        try:
                            audio = AudioSegment.from_file(str(file_path))
                            # Boost volume slightly for better audibility
                            audio = audio + 5  # +5dB
                            play(audio)
                            logger.info(f"✅ pydub playback completed: {file_path.name}")
                        except Exception as e:
                            logger.error(f"❌ pydub playback error: {e}")
                    
                    thread = threading.Thread(target=pydub_play, daemon=True)
                    thread.start()
                    
                    # Give it a moment to start
                    time.sleep(0.2)
                    
                    logger.info(f"✅ pydub playback started: {file_path.name}")
                    return {
                        "success": True,
                        "message": f"Playing audio file with pydub: {file_path.name}",
                        "method": "pydub",
                        "file_path": str(file_path.absolute())
                    }
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"❌ pydub error: {error_msg}")
                    
                    # Windows-specific error handling
                    if self.is_windows and ("263" in error_msg or "MCI" in error_msg):
                        mci_info = self._handle_windows_mci_error(error_msg)
                        logger.warning(f"🔧 Windows MCI issue detected: {mci_info['description']}")
            
            # Windows Emergency Fallback: winsound
            if self.is_windows and self._windows_audio_devices.get("winsound_available", False):
                logger.info("🆘 Trying Windows winsound emergency fallback...")
                winsound_result = self._windows_winsound_fallback(file_path)
                if winsound_result["success"]:
                    return winsound_result
                else:
                    logger.warning(f"⚠️ winsound fallback failed: {winsound_result.get('error')}")
            
            # If all methods fail
            logger.error(f"❌ All audio libraries failed for: {file_path.name}")
            
            # Enhanced error response with Windows-specific recommendations
            error_response = {
                "success": False,
                "error": "All audio playback methods failed",
                "file_path": str(file_path.absolute()),
                "available_libraries": self._audio_libraries,
                "recommendations": [
                    "Install missing audio libraries: pip install pygame sounddevice pydub simpleaudio scipy",
                    "Check if audio file format is supported (WAV recommended)",
                    "Verify system audio is working with other applications"
                ]
            }
            
            # Add Windows-specific recommendations
            if self.is_windows:
                error_response["windows_devices"] = self._windows_audio_devices
                error_response["recommendations"].extend([
                    "Try running as administrator",
                    "Update Windows audio drivers",
                    "Check Windows Audio service is running",
                    "Convert audio file to WAV format for better compatibility",
                    "Restart Windows Audio service: services.msc -> Windows Audio -> Restart"
                ])
            
            return error_response
            
        except Exception as e:
            logger.error(f"❌ Unexpected error in play_audio_file: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": str(file_path) if 'file_path' in locals() else "unknown"
            }
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about an audio file"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            stat = file_path.stat()
            info = {
                "success": True,
                "filename": file_path.name,
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2),
                "format": file_path.suffix.lower(),
                "full_path": str(file_path.absolute())
            }
            
            # Try to get additional audio info if pydub is available
            if self._audio_libraries.get('pydub', False):
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(str(file_path))
                    info.update({
                        "duration_ms": len(audio),
                        "duration_seconds": len(audio) / 1000.0,
                        "channels": audio.channels,
                        "sample_rate": audio.frame_rate,
                        "sample_width": audio.sample_width
                    })
                except Exception as e:
                    logger.warning(f"Could not get detailed audio info: {e}")
            
            return info
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_audio_files(self) -> Dict[str, Any]:
        """List all audio files in the output directory"""
        try:
            audio_extensions = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".aac"}
            audio_files = []
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                    stat = file_path.stat()
                    audio_files.append({
                        "filename": file_path.name,
                        "size_kb": round(stat.st_size / 1024, 2),
                        "format": file_path.suffix.lower(),
                        "full_path": str(file_path.absolute()),
                        "modified_time": stat.st_mtime
                    })
            
            # Sort by modification time (newest first)
            audio_files.sort(key=lambda x: x["modified_time"], reverse=True)
            
            return {
                "success": True,
                "count": len(audio_files),
                "files": audio_files,
                "output_directory": str(self.output_dir.absolute())
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_audio_system(self) -> Dict[str, Any]:
        """Test the audio system to verify it's working"""
        try:
            results = {
                "success": True,
                "library_tests": {},
                "recommendations": []
            }
            
            # Test each available library
            for lib_name, available in self._audio_libraries.items():
                if available:
                    try:
                        if lib_name == "pygame":
                            import pygame
                            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
                            pygame.mixer.init()
                            results["library_tests"][lib_name] = "✅ Initialized successfully"
                            pygame.mixer.quit()
                        
                        elif lib_name == "sounddevice":
                            import sounddevice as sd
                            devices = sd.query_devices()
                            results["library_tests"][lib_name] = f"✅ Found {len(devices)} audio devices"
                        
                        elif lib_name == "pydub":
                            from pydub import AudioSegment
                            results["library_tests"][lib_name] = "✅ Available for audio processing"
                        
                        elif lib_name == "simpleaudio":
                            import simpleaudio as sa
                            results["library_tests"][lib_name] = "✅ Available for WAV playback"
                            
                    except Exception as e:
                        results["library_tests"][lib_name] = f"❌ Error: {e}"
                        results["success"] = False
                else:
                    results["library_tests"][lib_name] = "❌ Not installed"
            
            # Add recommendations based on test results
            if not any(self._audio_libraries.values()):
                results["recommendations"].append("Install audio libraries: pip install pygame sounddevice pydub simpleaudio scipy")
                results["success"] = False
            
            if not self._audio_libraries.get('sounddevice', False):
                results["recommendations"].append("Install sounddevice for best cross-platform support: pip install sounddevice scipy")
            
            return results
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendations": ["Check Python environment and audio library installations"]
            }

# Backward compatibility - create an alias
AudioHandler = PurePythonAudioHandler

def main():
    """Command line interface for audio handler"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pure Python Audio Handler")
    parser.add_argument("action", choices=["play", "info", "list", "test"], 
                       help="Action to perform")
    parser.add_argument("--file", "-f", help="Audio file path (for play/info actions)")
    parser.add_argument("--output-dir", "-o", default="./output", 
                       help="Output directory path")
    
    args = parser.parse_args()
    
    handler = PurePythonAudioHandler(args.output_dir)
    
    if args.action == "play":
        if not args.file:
            print("Error: --file is required for play action")
            sys.exit(1)
        result = handler.play_audio_file(args.file)
    elif args.action == "info":
        if not args.file:
            print("Error: --file is required for info action")
            sys.exit(1)
        result = handler.get_audio_info(args.file)
    elif args.action == "list":
        result = handler.list_audio_files()
    elif args.action == "test":
        result = handler.test_audio_system()
    
    print(json.dumps(result, indent=2))
    
    if not result.get("success", False):
        sys.exit(1)

if __name__ == "__main__":
    main()