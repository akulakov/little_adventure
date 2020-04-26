#!/usr/bin/env python
from curses import wrapper, newwin
import curses
from copy import copy, deepcopy
from time import sleep
from random import random
from collections import defaultdict

rock = '▓'
blank = ' '
HEIGHT = 16
GROUND = HEIGHT-2   # ground level
BLOCKING = [rock]
LOAD_BOARD = 999
SLP = 0.01
debug_log = open('debug', 'w')
triggered_events = []
done_events = set()
boards = []
objects = {}


class Objects:
    obj = {}
    def __getitem__(self, id):
        return self.obj.get(id)
    def __setitem__(self, id, obj):
        self.obj[id] = obj

class Blocks:
    platform = '▁'
    bell = '🔔'
    door = '▕'
    grill = '▒'
    rubbish = '♽'
    truck = '🚚'
    locker = '🔲'
    grn_heart = '💚'
    coin = '🌕'

class Stance:
    normal = 1
    fight = 2
    sneaky = 3

class ID:
    platform1 = 1
    grill1 = 2
    alarm1 = 3
    door1 = 4
    grill2 = 5
    rubbish1 = 6
    truck1 = 7
    locker = 8
    coin = 9
    grn_heart = 10

    guard1 = 100
    technician1 = 101
    player = 102
    soldier1 = 103

def mkcell():
    return [blank]

def mkrow():
    return [mkcell() for _ in range(79)]

class Loc:
    def __init__(self, x, y):
        self.y, self.x = y, x

    def __iter__(self):
        yield self.x
        yield self.y
        # return iter((self.x, self.y))

    def __getitem__(self, i):
        return (self.x, self.y)[i]

    def __repr__(self):
        return str((self.x, self.y))

    def __eq__(self, l):
        return (self.x, self.y) == (l.x, l.y)

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
    def __init__(self, loc):
        self.B = B = [mkrow() for _ in range(HEIGHT)]
        bottom = B[-1]
        for cell in bottom:
            cell.append(rock)
        self.guards = []
        self.soldiers = []
        self.loc = loc

    def board_1(self):
        Item(self, Blocks.platform, 'mobile platform', Loc(15, GROUND), id=ID.platform1)
        g = Guard(self, Loc(15, GROUND), id=ID.guard1)
        self.guards = [g]

        self.put(rock, Loc(5, GROUND))
        self.put(rock, Loc(5, GROUND-1))
        for x in range(4):
            Item(self, Blocks.grill, 'grill', Loc(20+(x*4), GROUND))
        Item(self, Blocks.grill, 'grill', Loc(20+16, GROUND), id=ID.grill1)

        Item(self, Blocks.coin, 'coin', Loc(37,GROUND), id=ID.coin)
        c = Item(self, Blocks.locker, 'locker', Loc(40,GROUND), id=ID.locker)
        c.inv[ID.coin] += 1
        Item(self, Blocks.grn_heart, 'grn_heart', Loc(42,GROUND), id=ID.grn_heart)

        p = Player(self, Loc(45, GROUND), id=ID.player)
        objects[ID.player] = p
        return p

    def board_2(self):
        """Technician, alarm."""
        for x in range(5):
            row = self.B[-2-x]
            for cell in row[10+x:]:
                cell.append(rock)
        Technician(self, Loc(20, GROUND-5), id=ID.technician1)
        Item(self, Blocks.bell, 'alarm bell', Loc(25, GROUND-5), id=ID.alarm1)
        Item(self, Blocks.door, 'door', Loc(15, GROUND-5), id=ID.door1)

    def board_3(self):
        """Soldier, rubbish heap."""
        for x in range(5):
            row = self.B[-2-x]
            for cell in row[:5-x]:
                cell.append(rock)
        Item(self, Blocks.grill, 'grill', Loc(25, GROUND), id=ID.grill2)
        Item(self, Blocks.rubbish, 'rubbish', Loc(55, GROUND), id=ID.rubbish1)
        Item(self, Blocks.rubbish, 'rubbish', Loc(56, GROUND), id=ID.rubbish1)
        Item(self, Blocks.rubbish, 'rubbish', Loc(57, GROUND), id=ID.rubbish1)
        s = Soldier(self, Loc(70, GROUND), id=ID.soldier1)
        self.soldiers.append(s)

    def board_4(self):
        pass

    def __getitem__(self, loc):
        return self.B[loc.y][loc.x][-1]

    def __iter__(self):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                yield Loc(x,y), cell

    def get_all(self, loc):
        return [n for n in self.B[loc.y][loc.x] if n!=blank]

    def get_ids(self, loc):
        return ids(self.get_all(loc))

    def draw(self, win):
        for y, row in enumerate(self.B):
            for x, cell in enumerate(row):
                win.addstr(y,x, str(cell[-1]))
        # debug(self.B[-2])
        win.refresh()

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
    debug('chk_b_oob', loc.x, x)
    return 0 <= loc.y+y <= h-1 and 0 <= loc.x+x <= w-1

def ids(lst):
    return [x.id for x in lst if not isinstance(x, str)]

class Mixin1:
    is_player = 0

    def tele(self, loc):
        self.B.remove(self)
        self.put(loc)

    def put(self, loc):
        self.loc = loc
        self.B.put(self)
        if self.is_player and ID.platform1 in self.B.get_ids(loc):
            triggered_events.append(PlatformEvent1)


class Item(Mixin1):
    def __init__(self, B, char, name, loc=None, put=True, id=None):
        self.B, self.char, self.name, self.loc, self.id = B, char, name, loc, id
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __repr__(self):
        return self.char

    def move(self, dir):
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        new = self.loc.mod(*m)
        self.B.remove(self)
        self.loc = new
        self.B.put(self)


class Being(Mixin1):
    stance = Stance.normal
    health = 5
    is_being = 1
    is_player = 0
    hostile = 0
    kash = 0

    def __init__(self, B, loc=None, put=True, id=None):
        self.B = B
        self.id = id
        self.loc = loc
        self.inv = defaultdict(int)
        if id:
            objects[id] = self
        if put:
            B.put(self)

    def __str__(self):
        return self.char

    @property
    def fight_stance(self):
        return self.stance==Stance.fight

    @property
    def sneaky_stance(self):
        return self.stance==Stance.sneaky

    def _move(self, dir, fly=False):
        if dir == 'j' and not fly: return
        if dir == 'k' and not fly: return
        m = dict(h=(0,-1), l=(0,1), j=(1,0), k=(-1,0))[dir]
        if chk_oob(self.loc, *m):
            return True, self.loc.mod(*m)
        else:
            print("in _move self.B.loc", self.B.loc)
            if self.is_player and chk_b_oob(self.B.loc, *m):
                return LOAD_BOARD, self.B.loc.mod(*m)
        return 0, 0


    def move(self, dir, fly=False):
        B = self.B
        rv = self._move(dir, fly)
        if rv and (rv[0] == LOAD_BOARD):
            return rv
        new = rv[1]
        if new and isinstance(B[new], Being):
            if self.fight_stance or self.hostile:
                self.attack(B[new])
            else:
                self.switch_places()
            return True, True
        if new and B.is_blocked(new):
            new = new.mod(-1,0)
            if B.is_blocked(new):
                new = None
                if self.fight_stance:
                    Windows.win2.addstr(1, 0, 'BANG')
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

            pick_up = [ID.coin]
            B.remove(self)
            self.loc = new

            if self.is_player:
                items = B.get_all(new)
                for x in reversed(items):
                    print("x", x)
                    if x.id == ID.grn_heart:
                        self.health = min(10, self.health+1)
                        B.remove(x)
                    elif x.id in pick_up:
                        self.inv[x.id] += 1
                        B.remove(x)
                names = [i.name for i in B.get_all(new)]
                names = ', '.join(names)
                if names:
                    Windows.win2.addstr(2,0, f'You see: {names}')
            self.put(new)
            if ID.door1 in B.get_ids(self.loc):
                triggered_events.append(AlarmEvent1)
            grills = set((ID.grill1, ID.grill2))
            if self.sneaky_stance and (grills & set(B.get_ids(self.loc))):
                triggered_events.append(ClimbThroughGrillEvent1)

            Windows.win2.refresh()
            return True, True
        return None, None

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
            Windows.win2.addstr(1, 0, f'{self} hits {obj} for 1pt')
            if obj.is_being:
                obj.hostile = 1
            if obj.health <=0:
                self.B.remove(obj)
                if random()>0.6:
                    Item(self.B, Blocks.coin, 'one kash', obj.loc, id=ID.coin)
                elif random()>0.6:
                    Item(self.B, Blocks.grn_heart, 'heart', obj.loc, id=ID.grn_heart)

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

    def action(self):
        c = last( [x for x in self.B.get_all(self.loc) if x.id==ID.locker] )
        if c:
            for x in c.inv:
                self.inv[x] += c.inv[x]
                c.inv[x] = 0

def first(x):
    return x[0] if x else None
def last(x):
    return x[-1] if x else None

def pdb(stdscr):
    curses.nocbreak()
    stdscr.keypad(0)
    curses.echo()
    curses.endwin()
    import pdb; pdb.set_trace()

class Event:
    done = False
    once = 1
    def __init__(self, B):
        self.B = B

class GuardAttackEvent1(Event):
    def go(self):
        guard = objects[ID.guard1]
        if self.done: return
        guard.hostile = 1
        B = self.B
        mode = 1
        x, y = guard.loc
        platform = objects[ID.platform1]

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
            B.draw(Windows.win)
            sleep(SLP)
        self.done = True

class PlatformEvent1(Event):
    def go(self):
        debug('PlatformEvent1 start')
        if self.done: return
        player = objects[ID.player]
        B = self.B
        mode = 1
        x, y = player.loc
        platform = objects[ID.platform1]

        debug('y', y)
        for _ in range(35):
            debug('y', y, 'mode', mode, 'height-10', HEIGHT-10)
            if mode==1:
                if y>=(HEIGHT-10):
                    platform.move('k')
                    player.move('k', fly=1)
                    y = player.loc.y
                else:
                    mode = 2

            elif mode==2:
                if x<15:
                    platform.move('l')
                    player.move('l', fly=1)
                    x = player.loc.x
                else:
                    mode = 3
            elif mode==3:
                if y<GROUND:
                    platform.move('j')
                    player.move('j', fly=1)
                    y = player.loc.y
                else:
                    mode = 4

            elif mode==4:
                break
            B.draw(Windows.win)
            sleep(SLP)
        self.done = True

class ClimbThroughGrillEvent1(Event):
    once = False
    def go(self):
        player = objects[ID.player]
        B = self.B
        B.remove(player)
        bi = B.loc.x
        B = boards[0][2 if bi==0 else 0]
        player.loc = Loc(25 if bi==0 else 36, GROUND)
        B.put(player)
        B.draw(Windows.win)
        player.B = B
        Windows.win2.addstr(2,0, 'You climb through the grill into a space that opens into an open area outside the building')
        return B

class AlarmEvent1(Event):
    def go(self):
        if self.done: return
        B = self.B
        tech = objects[ID.technician1]
        x, y = tech.loc
        ok = 0
        player = objects[ID.player]

        for _ in range(35):
            tech.move('l')
            platform1 = objects[ID.platform1]

            if ID.alarm1 in B.get_ids(tech.loc):
                Windows.win2.addstr(2,0, '!ALARM!')
                B.remove(player)
                B = boards[0][0]
                player.B = B
                player.put(Loc(0, GROUND))
                platform1.tele(Loc(15, GROUND))
                objects[ID.guard1].tele(Loc(15, GROUND))
                ok = 1
            B.draw(Windows.win)
            if ok: break
            sleep(0.1)
        self.done = True
        return B

class GarbageTruckEvent(Event):
    def go(self):
        B=self.B
        if self.done: return
        t = Item(B, Blocks.truck, 'Garbage truck', Loc(78, GROUND))
        dir = 'h'
        pl = objects[ID.player]
        for _ in range(45):
            t.move(dir)
            if t.loc == pl.loc:
                dir = 'l'
                B.remove(pl)
                Windows.win2.addstr(2,0, 'The truck suddenly picks you up along with the rubbish!')
            if t.loc.x==78:
                B.remove(t)
                B.draw(Windows.win)
                break
            B.draw(Windows.win)
            sleep(SLP)

class Player(Being):
    char = '@'
    health = 10
    is_player = 1
    stance = Stance.sneaky

class Guard(Being):
    char = 'g'
    health = 3

class Soldier(Being):
    health = 20
    char = 's'

class Technician(Being):
    char = 't'

class NPCs:
    pass
class OtherBeings:
    pass

class Saves:
    saves = {}
    loaded = 0

    def save(self, name, cur_brd):
        s = {}
        s['boards'] = deepcopy(boards)
        s['beings'] = deepcopy(OtherBeings)
        s['cur_brd'] = cur_brd
        s['player'] = deepcopy(objects[ID.player])
        self.saves[name] = s

    def load(self, name):
        s = self.saves[name]
        boards[:] = s['boards']
        loc = s['player'].loc
        bl = s['cur_brd']
        B = boards[bl.y][bl.x]
        player = B[loc]
        player.B = B
        return player, B

class Windows:
    pass

def dist(a,b):
    return max(abs(a.loc.x - b.loc.x),
               abs(a.loc.y - b.loc.y))

def main(stdscr):
    begin_x = 0; begin_y = 0; width = 80
    win = Windows.win = newwin(HEIGHT, width, begin_y, begin_x)
    begin_x = 0; begin_y = 16; height = 6; width = 80
    win2 = Windows.win2 = newwin(height, width, begin_y, begin_x)
    B = b1 = Board(Loc(0,0))
    b2 = Board(Loc(1,0))
    b3 = Board(Loc(2,0))

    player = b1.board_1()
    b2.board_2()
    b3.board_3()
    boards.append([b1, b2, b3])

    stdscr.clear()
    B.draw(win)

    win2.addstr(0, 0, '-'*80)
    win2.refresh()

    Saves().save('start', B.loc)
    last_cmd = None
    wait_count = 0

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
            rv = player.move(k)
            if rv[0] == LOAD_BOARD:
                loc = rv[1]
                B.remove(player)
                B = boards[loc.y][loc.x]
                player.loc.x = 0 if k=='l' else 78
                B.put(player)
                player.B = B

        elif k == '.':
            if last_cmd=='.':
                wait_count += 1
            if wait_count >= 5 and ID.rubbish1 in B.get_ids(player.loc):
                triggered_events.append(GarbageTruckEvent)
            debug(str(triggered_events))
        elif k == 's':
            player.switch_places()
        elif k == 'S':
            player.stance = Stance.sneaky
            win2.addstr(1, 0, 'stance: sneaky')
        elif k == 'L':
            player, B = Saves().load('start')
            objects[ID.player] = player
        elif k == 'i':
            pass
        elif k == ' ':
            player.action()

        if k != '.':
            wait_count = 0
        last_cmd = k

        B.guards = [g for g in B.guards if g.health>0]
        B.soldiers = [g for g in B.soldiers if g.health>0]
        for g in B.guards:
            if g.hostile:
                g.attack(player)
        for s in B.soldiers:
            if s.hostile or dist(s, player) <= 5:
                s.hostile = 1
                s.attack(player)

        if player.health <= 0:
            win2.addstr(1, 0, f'Hmm.. it looks like you lost the game!')
            player, B = Saves().load('start')
            objects[ID.player] = player

        B.draw(win)
        win2.addstr(0,0, f'[H{player.health}] [${player.inv[ID.coin]}]')
        win2.refresh()

        for evt in triggered_events:
            debug(evt)
            if evt in done_events and evt.once:
                continue
            rv = evt(B).go()
            if isinstance(rv, Board):
                B = rv
            done_events.add(evt)

        triggered_events.clear()
        print("player.loc", player.loc)


def debug(*args):
    debug_log.write(str(args) + '\n')
    debug_log.flush()
print=debug

if __name__ == "__main__":
    wrapper(main)
