import pathlib

import aiohttp

token = 'TOKEN'

async def download_by_chunks_large(url: str, destination):
    print('⬇️ Start Dwonloading by Chunks')
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            with open(destination, 'wb') as f:
                # Download in chunks (e.g., 1MB per chunk)
                while True:
                    chunk = await response.content.read(64 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)


async def make_file_download_zero(media_obj: any, file_size: int, path_media_obj: pathlib.Path):
    print('⬇️ Start Dwonloading')

    print('FILE ID: ')
    print(media_obj.file_id)

    _file = None
    try:
        _file = await media_obj.get_file()
    except Exception as e:
        print('🔴 Cant get_file: Exit', e)
        print()
        return

    if file_size < 20000000:
        try:
            await _file.download_to_drive(path_media_obj)
        except Exception as e:
            print(f"2-Error downloading file to {path_media_obj}: {e}")
            return
    else:
        print('Down Large: ')
        print(media_obj.file_id)

        url = f'https://api.telegram.org/file/bot{token}/{media_obj.file_id}'
        print('url: ')
        print(url)
        print()

        try:
            await download_by_chunks_large(url, path_media_obj)
        except Exception as e:
            print(f"3-Error downloading file to {path_media_obj}: {e}")
            return
    print('⬇️ End Dwonloading')

    return path_media_obj
