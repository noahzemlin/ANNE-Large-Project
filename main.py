from agent import Agent
import traceback
import signal
from simulator import SimulationThread
import curses
from world import World
from render import RenderThread

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
    window = curses.newwin(height, width, 0, 0)
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

    world = World()
    world.from_file("basic.wrld")
    sc, window = create_window(world.width, world.height)

    agent1 = Agent(4, [4, 4], 4)

    world.put_agent(agent1, 2, world.height//3 * 2)

    sim_thread = SimulationThread(world)
    render_thread = RenderThread(window, world)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGSEGV, signal_handler)

    render_thread.start()
    sim_thread.start()

    render_thread.join()
    sim_thread.running = False
    sim_thread.join()

if __name__ == '__main__':
    try:
        main()
    except BaseException as e:
        signal_handler(None, None)
        traceback.print_exc()