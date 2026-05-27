import os


def get_playlists_dir(base_file):
    return os.path.join(os.path.dirname(base_file), "..", "playlists")


def ensure_playlists_dir(playlists_dir):
    if not os.path.exists(playlists_dir):
        os.makedirs(playlists_dir)
