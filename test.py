#!/usr/bin/env python
from curses import wrapper, newwin
from copy import copy
from time import sleep

rock = '▓'
blank = ' '
HEIGHT = 16
GROUND = HEIGHT-2   # ground level
BLOCKING = [rock]
SLP = 0.01
debug_log = open('debug', 'w')
triggered_events = []
done_events = set()
boards = []

class Blocks:
    platform = '▁'
    bell = '🔔'
    door = '▕'

class Stance:
    normal = 1
    fight = 2

def mkcell():
    return [blank]

def mkrow():
    return [mkcell() for _ in range(79)]

class Loc:
    def __init__(self, x, y):
        self.y, self.x = y, x

    def __iter__(self):
        return iter((self.x, self.y))

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __str__(self):
        return str((self.x, self.y))

    def mod(self, y, x):
        new = copy(self)
        new.y += y
        new.x += x
        return new

    def mod_r(self):
        return self.mod(0, 1)

    def mod_l(self):
        return self.mod(0, -1)

class Board:
    brd_index = Loc(0,0)

    def __init__(self):
        self.B = B = [mkrow() for _ in range(HEIGHT)]
        bottom = B[-1]
        for cell in bottom:
            cell.append(rock)

    def board_2(self):
        for x in range(5):
            row = self.B[-2-x]
            for cell in bottom[10+x:]:
                cell.append(rock)
        tech = Technician(self, Loc(15, GROUND-5))
        alarm = Item(self, Blocks.bell, Loc(15, GROUND-5))
        return tech, alarm

    def __getitem__(self, loc):
        return self.B[loc.y][loc.x][-1]

    def get_all(self, loc):
        return self.B[loc.y][loc.x]

    def draw(self, win):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                win.addstr(y,x, str(cell[-1]))

    def put(self, obj, loc=None):
        loc = loc or obj.loc
        self.B[loc.y][loc.x].append(obj)

    def remove(self, obj, loc=None):
        loc = loc or obj.loc
        self.B[loc.y][loc.x].remove(obj)

    def is_blocked(self, loc):
        return self[loc] in BLOCKING

    def avail(self, loc):
        return not self.is_blocked(loc)



def chk_oob(loc, y=0, x=0):
    return 0 <= loc.y+y <= HEIGHT-1 and 0 <= loc.x+x <= 78

def chk_b_oob(loc, y=0, x=0):
    h = len(boards)
    w = len(boards[0])
    return 0 <= loc.y+y <= h-1 and 0 <= loc.x+x <= w-1

class Mixin1:
    is_player = 0

    def tele(self, loc):
        self.B.remove(self)
        self.put(loc)

    def put(self, loc):
        self.loc = loc
        self.B.put(self)
        if self.is_player and platform in self.B.get_all(loc):
            triggered_events.append(PlatformEvent1)


class Item(Mixin1):
    def __init__(self, B, char, loc=None):
        self.B, self.char, self.loc = B, char, loc

    def __str__(self):
        return self.char

    def move(self, B, dir):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        new = self.loc.mod(*m)
        B.remove(self)
        self.loc = new
        B.put(self)

LOAD_BOARD = 999

class Being(Mixin1):
    stance = Stance.normal
    health = 5
    is_being = 1
    is_player = 0
    hostile = 0

    def __init__(self, B, loc=None, win=None, win2=None):
        self.B = B
        self.loc = loc
        self.win = win
        self.win2 = win2

    def __str__(self):
        return self.char

    @property
    def fight_stance(self):
        return self.stance==Stance.fight

    def _move(self, dir, fly=False):
        if dir == 'j' and not fly: return
        if dir == 'k' and not fly: return
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        if chk_oob(self.loc, *m):
            if chk_b_oob(self.B.brd_index, *m):
                return LOAD_BOARD, self.B.brd_index.mod(*m)

            return self.loc.mod(*m)


    def move(self, dir, fly=False):
        B = self.B
        old = copy(self.loc)
        rv = self._move(dir, fly)
        if rv[0] == LOAD_BOARD:
            return rv
        new = rv
        if new and isinstance(B[new], Being):
            if self.fight_stance or self.hostile:
                self.attack(B[new])
            else:
                self.switch_places()
            return True
        if new and B.is_blocked(new):
            new = new.mod(-1,0)
            if B.is_blocked(new):
                new = None
                if self.fight_stance:
                    self.win2.addstr(1, 0, 'BANG')
                    triggered_events.append(GuardAttackEvent1)

        if new:
            if not fly:
                # fall
                new2 = new
                while 1:
                    new2 = new2.mod(1,0)
                    if chk_oob(new2) and B.avail(new2):
                        new = new2
                    else:
                        break

            B.remove(self)
            self.loc = new
            self.put(new)
            if door1 in B.get_all(self.loc):
                triggered_events.append(AlarmEvent1)

            if self.win2:
                # self.win2.addstr(2,0,f'moving {self} to {new}')
                self.win2.refresh()
            return True

    def attack(self, obj):
        if abs(self.loc.x - obj.loc.x) <= 1 and \
           abs(self.loc.y - obj.loc.y) <= 1:
                self.hit(obj)
        else:
            if self.loc.x < obj.loc.x:
                self.move('l')
            else:
                self.move('h')

    def hit(self, obj):
        if obj.health:
            obj.health -= 1
            self.win2.addstr(1, 0, f'{self} hits {obj} for 1pt')

    def switch_places(self):
        B = self.B
        r,l = self.loc.mod_r(), self.loc.mod_l()
        ro = lo = None
        if chk_oob(r): ro = B[r]
        if chk_oob(l): lo = B[l]

        if isinstance(ro, Being):
            B.remove(ro)
            B.remove(self)
            loc = self.loc
            self.put(r)
            ro.put(loc)

        if isinstance(lo, Being):
            B.remove(lo)
            B.remove(self)
            loc = self.loc
            self.put(l)
            lo.put(loc)


class Event:
    done = False
    once = 1
    def __init__(self, B, win):
        self.B, self.win = B, win

class GuardAttackEvent1(Event):
    def go(self, platform, guard):
        if self.done: return
        guard.hostile = 1
        B = self.B
        mode = 1
        x, y = guard.loc

        for _ in range(35):
            if mode==1:
                if y>=HEIGHT-10:
                    platform.move(B, 'k')
                    guard.move('k', fly=1)
                    y = guard.loc.y
                else:
                    mode = 2
            elif mode==2:
                if x>=3:
                    platform.move(B, 'h')
                    guard.move('h', fly=1)
                    x = guard.loc.x
                else:
                    mode = 3
            elif mode==3:
                if y<GROUND:
                    platform.move(B, 'j')
                    guard.move('j', fly=1)
                    y = guard.loc.y
                else:
                    mode = 4
            elif mode==4:
                break
            B.draw(self.win)
            self.win.refresh()
            sleep(SLP)
        self.done = True

class PlatformEvent1(Event):
    def go(self, platform, player):
        debug('PlatformEvent1 start')
        if self.done: return
        B = self.B
        mode = 1
        x, y = player.loc

        debug('y', y)
        for _ in range(35):
            debug('y', y, 'mode', mode, 'height-10', HEIGHT-10)
            if mode==1:
                if y>=(HEIGHT-10):
                    platform.move(B, 'k')
                    player.move('k', fly=1)
                    y = player.loc.y
                else:
                    mode = 2

            elif mode==2:
                if x<15:
                    platform.move(B, 'l')
                    player.move('l', fly=1)
                    x = player.loc.x
                else:
                    mode = 3
            elif mode==3:
                if y<GROUND:
                    platform.move(B, 'j')
                    player.move('j', fly=1)
                    y = player.loc.y
                else:
                    mode = 4

            elif mode==4:
                break
            B.draw(self.win)
            self.win.refresh()
            sleep(SLP)
        self.done = True

class AlarmEvent1(Event):
    def go(self, win2, guard, tech, player):
        if self.done: return
        B = self.B
        x, y = tech.loc
        ok = 0

        for _ in range(35):
            tech.move('l')
            if alarm1 in B.get_all(tech.loc):
                win2.addstr(2,0, '!ALARM!')
                player.tele(Loc(0, GROUND))
                guard.tele(Loc(15, GROUND))
                platform.tele(Loc(15, GROUND))

                ok = 1
            B.draw(self.win)
            self.win.refresh()
            if ok: break
            sleep(0.1)
        self.done = True

class Player(Being):
    char = '@'
    health = 10
    is_player = 1

class Guard(Being):
    char = 'g'

class Technician(Being):
    char = 't'

def main(stdscr):
    begin_x = 0; begin_y = 0; width = 80
    win = newwin(HEIGHT, width, begin_y, begin_x)
    begin_x = 0; begin_y = 16; height = 6; width = 80
    global platform, door1, alarm1
    win2 = newwin(height, width, begin_y, begin_x)
    B = Board()
    b2 = Board()
    b2.board_2()
    boards.append([B, b2])

    loc = Loc(0, GROUND)
    player = Player(B, loc, win, win2)
    B.put(player)
    guard1 = Guard(B, Loc(15, GROUND), win, win2)
    technician1 = Technician(B, Loc(25, GROUND), win, win2)
    B.put(guard1)
    B.put(technician1)
    guards = [guard1, technician1]

    B.put(rock, Loc(5, GROUND))
    B.put(rock, Loc(5, GROUND-1))
    platform = Item(B, Blocks.platform, Loc(15, GROUND))
    alarm1 = Item(B, Blocks.bell, Loc(30, GROUND))
    door1 = Item(B, Blocks.door, Loc(20, GROUND))
    B.put(platform)
    B.put(alarm1)
    B.put(door1)

    stdscr.clear()
    B.draw(win)
    win.refresh()

    win2.addstr(0, 0, '-'*80)
    win2.refresh()

    while 1:
        k = win.getkey()
        win2.clear()
        win2.addstr(2,0,k)
        if k=='q':
            return
        elif k=='f':
            player.stance = Stance.fight
            win2.addstr(1, 0, 'stance: fight')
        elif k=='n':
            player.stance = Stance.normal
            win2.addstr(1, 0, 'stance: normal')
        elif k in 'hl':
            player.move(k)
        elif k == '.':
            debug(str(triggered_events))
        elif k == 's':
            player.switch_places()

        for g in guards:
            if g.hostile:
                g.attack(player)
        B.draw(win)
        win.refresh()
        win2.refresh()

        for evt in triggered_events:
            debug(evt)
            if evt in done_events and evt.once:
                continue
            e = evt(B, win)
            if isinstance(e, GuardAttackEvent1):
                e.go(platform, guard1)
            elif isinstance(e, PlatformEvent1):
                e.go(platform, player)
            elif isinstance(e, AlarmEvent1):
                e.go(win2, guard1, technician1, player)
            done_events.add(evt)

        triggered_events.clear()

def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
    # win2.addstr(2,0, str(args))

if __name__ == "__main__":
    wrapper(main)
