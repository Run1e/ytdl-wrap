import click
import os
import subprocess
import shlex

from urllib.parse import urlparse, parse_qs

import config
from utils import ensure_folder, subfolders


def create_runnable(query, output=None, archive=None):
	state = config.YOUTUBE_BIN

	if output is not None:
		state += ' --output "{}"'.format(output)
	if archive is not None:
		state += ' --download-archive "{}"'.format(archive)

	for subquery in query:
		state += ' "{}"'.format(subquery)

	return state


def update_channels():
	# get channels folder and stop if it doesn't exist
	channels_folder = os.path.abspath(os.path.join(config.BASE_FOLDER, 'channels'))
	if not os.path.isdir(channels_folder):
		return

	# create a set of all channel URLs
	users = set('https://www.youtube.com/user/{}'.format(folder) for folder in subfolders(channels_folder))

	# stop if none...
	if not users:
		click.echo('No channel folders found, stopping update.')
		return

	# create runnable for this channel and run it
	runnable = create_runnable(
		query=users,
		output=os.path.join(channels_folder, '%(uploader_id)s', config.CHANNEL_FORMAT),
		archive=os.path.join(channels_folder, 'archive')
	)

	subprocess.run(runnable, shell=True)


def update_playlists():
	# get playlists folder, stop if nonexistent
	playlists_folder = os.path.abspath(os.path.join(config.BASE_FOLDER, 'playlists'))
	if not os.path.isdir(playlists_folder):
		return

	# loop through it, formatting the url and just invoking the playlist cli command
	for folder in subfolders(playlists_folder):
		playlist(('https://www.youtube.com/playlist?list={}'.format(folder),))


@click.group(invoke_without_command=True)
def cli():
	pass


@cli.command()
def update():
	update_playlists()
	update_channels()


@cli.command()
@click.argument('query', nargs=-1)
def channel(query):
	# find and ensure the channels folder
	channels_folder = os.path.abspath(os.path.join(config.BASE_FOLDER, 'channels'))
	ensure_folder(channels_folder)

	runnable = create_runnable(
		query=query,
		archive=os.path.join(channels_folder, 'archive'),  # global channels archive
		output=os.path.join(channels_folder, '%(uploader_id)s', config.CHANNEL_FORMAT))  # set full output format

	# run youtube-dl
	subprocess.run(runnable, shell=True)


@cli.command()
@click.argument('playlist_url')
def playlist(playlist_url):
	print(playlist_url)

	# try parsing the playlist url
	try:
		parsed = urlparse(playlist_url)
	except ValueError:
		click.echo('Failed parsing playlist url, stopping.')
		return

	# parse the query string
	query_dict = parse_qs(parsed.query)

	# try to get the playlist id out from it
	try:
		playlist_id = query_dict['list'][0]
	except KeyError:
		click.echo('Invalid playlist url, stopping.')
		return

	# create/get playlists folder
	playlists_folder = os.path.abspath(os.path.join(config.BASE_FOLDER, 'playlists'))
	ensure_folder(playlists_folder)

	# create/get playlist output folder
	output_folder = os.path.join(playlists_folder, playlist_id)
	ensure_folder(output_folder)

	runnable = create_runnable(
		query=[playlist_url],
		output=os.path.join(output_folder, config.PLAYLIST_FORMAT),
		archive=os.path.join(output_folder, 'archive'))

	subprocess.run(runnable, shell=True)


@cli.command()
@click.argument('group_name')
@click.argument('query', default=None, nargs=-1)
def group(group_name, query):
	# create/get groups folder(s)
	group_folder = os.path.abspath(os.path.join(config.BASE_FOLDER, 'groups'))
	ensure_folder(group_folder)

	group_folder = os.path.join(group_folder, group_name)
	ensure_folder(group_folder)

	# if no query is specified, just create the folder and exit
	if not query:
		click.echo('Group folder created.')
		return

	archive = os.path.join(group_folder, 'archive')

	runnable = create_runnable(
		query=query,
		archive=archive,
		output=os.path.join(group_folder, config.GROUP_FORMAT))

	subprocess.run(runnable, shell=True)


if __name__ == '__main__':
	# create base folder if it doesn't exist
	ensure_folder(config.BASE_FOLDER)

	# start the click cli
	cli()
