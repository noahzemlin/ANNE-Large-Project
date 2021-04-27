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

sim_thread = render_thread = sc = None

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

    curses.nocbreak()

    if sc is not None:
        sc.keypad(False)

    curses.echo()

    curses.endwin()

def main():
    global sim_thread, render_thread, sc

    logging.basicConfig(filename='log.log', filemode='w', level=logging.DEBUG, format='%(levelname)s %(asctime)s: %(message)s', datefmt='%H:%M:%S')

    logging.info("Loading World")
    world = World()
    world.from_file("basic.wrld")

    logging.info("Making Window")
    sc, window = create_window(world.width, world.height)

    logging.info("Creating Threads")
    sim_thread = SimulationThread(world)
    render_thread = RenderThread(window, sim_thread)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)

    logging.info("Starting Threads")
    render_thread.start()
    sim_thread.start()

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