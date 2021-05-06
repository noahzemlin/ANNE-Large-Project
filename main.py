from numpy.core.fromnumeric import trace
from agent import Agent
import traceback
import signal
from simulator import SimulationThread
import curses
from world import World
from render import RenderThread
import logging
import sys
import argparse

sim_thread = render_thread = sc = None
display_graphics = False

def create_window(width, height):
    # Init screen
    sc = curses.initscr()
    curses.noecho()
    curses.start_color()

    # Create colors
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)

    # Create window
    window = curses.newwin(height+1, width, 0, 0)
    window.keypad(1)
    curses.curs_set(0)

    return sc, window

# Clean up everything
def signal_handler(sig, frame):
    if sim_thread is not None:
        sim_thread.running = False
    if render_thread is not None:
        render_thread.running = False

    if display_graphics:
        curses.nocbreak()

        if sc is not None:
            sc.keypad(False)

        curses.echo()

        curses.endwin()

def parse_args():
    parser = argparse.ArgumentParser(description='Evolution epic')
    parser.add_argument('-display_graphics', action='store_true', default=False)
    parser.add_argument('-exp_index', type=int, default=1)

    return parser.parse_args()

def main():
    global sim_thread, render_thread, sc, display_graphics

    args = parse_args()

    display_graphics = args.display_graphics

    logging.basicConfig(filename=f'log_{args.exp_index}.log', filemode='w', level=logging.DEBUG, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%H:%M:%S')

    logging.info("Loading World")
    world = World()
    world.from_file("basic.wrld")

    if display_graphics:
        logging.info("Making Window")
        sc, window = create_window(world.width, world.height)

    logging.info("Creating Threads")
    sim_thread = SimulationThread(world, exp=args.exp_index)

    if display_graphics:
        render_thread = RenderThread(window, sim_thread)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)

    logging.info("Starting Threads")

    if display_graphics:
        render_thread.start()

    sim_thread.start()

    if display_graphics:
        render_thread.join()
        logging.info("Render Thread Complete")
        sim_thread.running = False

    sim_thread.join()
    logging.info("Simulation Thread Complete")

if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        signal_handler(None, None)
        traceback.print_exc()