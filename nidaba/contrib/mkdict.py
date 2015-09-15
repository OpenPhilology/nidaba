#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, absolute_import

import click

from nidaba import lex


@click.command()
@click.option('--input', help='Input text', type=click.Path(exists=True,
              dir_okay=False), required=True)
@click.option('--del_dict', help='Path to the output deletion dictionary',
              type=click.Path(writable=True, dir_okay=False), required=True)
@click.option('--dictionary', help='Path to the output word list',
              type=click.Path(writable=True, dir_okay=False), required=True)
@click.option('--depth', default=1, help='Maximum precalculated edit distance '
              'in deletion dictionary')
@click.version_option()
def main(input, del_dict, dictionary, depth):
    click.echo('Reading input file\t[', nl=False)
    words = lex.cleanuniquewords(input)
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
    click.echo('Writing dictionary\t[', nl=False)
    lex.make_dict(dictionary, words)
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
    click.echo('Writing deletions\t[', nl=False)
    lex.make_deldict(del_dict, words, depth)
    click.secho(u'\u2713', fg='green', nl=False)
    click.echo(']')
