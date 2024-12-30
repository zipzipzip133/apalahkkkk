import requests
import re
import time
import os
import urllib.parse

async def handle_mediafire(event, client):
    mediafire_url = event.pattern_match.group(1).strip()
    loading_msg = await event.respond("```🔄 Sedang memproses URL MediaFire...```")

    try:
        # Header HTTP dengan user-agent lengkap
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-CH-UA-Platform": "\"Android\"",
            "Sec-CH-UA-Mobile": "?1",
            "Sec-CH-UA": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "Save-Data": "on",
            "Accept-Language": "id,en-US;q=0.9,en;q=0.8,ms;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }

        # Ambil konten HTML dari URL pertama
        response_1 = requests.get(mediafire_url, headers=headers)
        response_1.raise_for_status()
        html_content_1 = response_1.text

        # Ekstrak URL dari respons pertama
        first_pattern = r'<a[^>]*class=["\']input popsok["\'][^>]*href=["\']([^"\']+)["\']'
        match_1 = re.search(first_pattern, html_content_1, re.IGNORECASE)
        if not match_1:
            await loading_msg.edit("```❌ Gagal menemukan link pertama di MediaFire.```")
            return

        first_download_link = "https:" + match_1.group(1)

        # Ambil konten HTML dari URL kedua
        response_2 = requests.get(first_download_link, headers=headers)
        response_2.raise_for_status()
        html_content_2 = response_2.text

        # Ekstrak URL unduhan dan ukuran file dari respons kedua
        second_pattern = r'<a[^>]*class=["\']input popsok["\'][^>]*href=["\']([^"\']+)["\'][^>]*>\s*Download\s*\(([^)]+)\)'
        match_2 = re.search(second_pattern, html_content_2, re.IGNORECASE)
        if not match_2:
            await loading_msg.edit("```❌ Gagal menemukan link unduhan pada respons kedua.```")
            return

        second_download_link = "https:" + match_2.group(1) if not match_2.group(1).startswith('https://') else match_2.group(1)
        file_size = match_2.group(2)

        # Informasi unduhan
        await loading_msg.edit(
            f"```📥 Link: {second_download_link}\n"
            f"📦 Ukuran: {file_size}\n\n"
            f"🔄 Sedang mengunduh file...```"
        )

        # Unduh file
        file_name = second_download_link.split('/')[-1].split('?')[0]
        file_name = urllib.parse.unquote(file_name)
        response_file = requests.get(second_download_link, stream=True)
        total_size = int(response_file.headers.get('content-length', 0))
        chunk_size = 262144  # 256 KB
        downloaded = 0
        start_time = time.time()
        last_update_time = time.time()

        with open(file_name, "wb") as file:
            for data in response_file.iter_content(chunk_size):
                file.write(data)
                downloaded += len(data)
                elapsed_time = time.time() - start_time
                speed = downloaded / elapsed_time / 1024  # KB/s
                eta = (total_size - downloaded) / (speed * 1024) if speed > 0 else 0

                # Update progress setiap 1 detik
                if time.time() - last_update_time > 1:
                    await loading_msg.edit(
                        f"```📥 Link: {second_download_link}\n"
                        f"📦 Ukuran: {file_size}\n\n"
                        f"🚀 Kecepatan: {speed:.2f} KB/s\n"
                        f"📂 Progres: {downloaded / 1024 / 1024:.2f}/{total_size / 1024 / 1024:.2f} MB\n"
                        f"⏳ ETA: {eta:.2f} detik```"
                    )
                    last_update_time = time.time()

        # Kirim file langsung sesuai hasil unduhan
        await client.send_file(
            event.chat_id, 
            file_name, 
            caption="📂 File berhasil diunduh."
        )
        os.remove(file_name)  # Hapus file setelah dikirim
        await loading_msg.delete()  # Hapus pesan status

    except Exception as e:
        await loading_msg.edit(f"```❌ Terjadi kesalahan: {str(e)}```")
