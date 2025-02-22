from video_utils import generate_video_url, check_video_status
import time

text_input = "test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test "

job_id = generate_video_url(text_input)

if job_id is None:
    print("❌ Failed to initiate video generation. Check logs for details.")
else:
    print(f"✅ Video generation started. Job ID: {job_id}")

    retries = 0
    max_retries = 60  # 🔥 More retries to give webhook time
    time.sleep(10)  # 🔥 Wait longer before first status check

    while retries < max_retries:
        status, video_url = check_video_status(job_id)
        print(f"🔍 Checked status: {status}, Video URL: {video_url}")

        if status == "completed":
            print(f"🎥 Video Generated: {video_url}")
            break
        elif status == "unknown":
            print("❓ Job status unknown. Waiting for webhook...")
            retries += 1
            time.sleep(5)  # 🔥 Keep retrying to allow time for webhook
        elif status == "failed":
            print("❌ Video generation failed.")
            break
        else:
            print("⏳ Video generation in progress...")
            retries += 1
            time.sleep(5)

    else:
        print("❌ Video generation failed after maximum retries.")