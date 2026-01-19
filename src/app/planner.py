import heapq
import math


class AStarPlanner:
    def __init__(self, grid, resolution, origin_x, origin_y):
        self.grid = grid  # Matricea 0/1 (Liber/Zid)
        self.resolution = resolution
        self.origin_x = origin_x
        self.origin_y = origin_y
        self.height = len(grid)
        self.width = len(grid[0])

    def world_to_grid(self, wx, wy):
        """ Converteste coordonate Reale (Metri) in coordonate Matrice (Index) """
        gx = int((wx - self.origin_x) / self.resolution)
        gy = int((wy - self.origin_y) / self.resolution)
        return gx, gy

    def grid_to_world(self, gx, gy):
        """ Converteste coordonate Matrice (Index) in coordonate Reale (Metri) """
        wx = (gx * self.resolution) + self.origin_x
        wy = (gy * self.resolution) + self.origin_y
        return wx, wy

    def find_nearest_walkable(self, start_gx, start_gy, max_radius=10):
        """
        Daca robotul sau tinta se afla intr-un zid (eroare GPS),
        cautam cel mai apropiat punct liber din jur.
        """
        for r in range(1, max_radius + 1):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx, ny = start_gx + dx, start_gy + dy
                    # Verificam limitele hartii
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        # Daca gasim un punct liber (0), il returnam
                        if self.grid[ny][nx] == 0:
                            return nx, ny
        return None

    def plan(self, start_x, start_y, goal_x, goal_y):
        """
        Implementarea algoritmului A* (A-Star).
        Gaseste cel mai scurt drum de la Start la Goal.
        """
        # Convertim metri in indecsi de grid
        start_node = self.world_to_grid(start_x, start_y)
        goal_node = self.world_to_grid(goal_x, goal_y)

        print(f"[PLANNER] Calcul ruta: Start{start_node} -> Goal{goal_node}")

        # 1. Validari si Corectii de siguranta
        # Daca startul e in zid, mutam startul langa zid
        if not (0 <= start_node[0] < self.width and 0 <= start_node[1] < self.height): return []
        if self.grid[start_node[1]][start_node[0]] == 1:
            print("[PLANNER] Start blocat. Caut punct valid...")
            new_start = self.find_nearest_walkable(start_node[0], start_node[1])
            if new_start:
                start_node = new_start
            else:
                return []

        # Daca tinta e in zid (ex: in mijlocul unui scaun), mutam tinta langa scaun
        if not (0 <= goal_node[0] < self.width and 0 <= goal_node[1] < self.height): return []
        if self.grid[goal_node[1]][goal_node[0]] == 1:
            print(f"[PLANNER] Tinta blocata. Caut punct valid...")
            new_goal = self.find_nearest_walkable(goal_node[0], goal_node[1])
            if new_goal:
                goal_node = new_goal
            else:
                return []

        # 2. Initializare A*
        open_set = []
        heapq.heappush(open_set, (0, start_node))  # Coada de prioritati
        came_from = {}  # Pentru reconstructia drumului
        g_score = {start_node: 0}  # Costul de la start pana aici
        f_score = {start_node: self.heuristic(start_node, goal_node)}  # Cost estimat total

        while open_set:
            # Extragem nodul cu cel mai mic scor F
            current = heapq.heappop(open_set)[1]

            # Daca am ajuns la final, reconstruim drumul
            if current == goal_node:
                return self.reconstruct_path(came_from, current)

            # Definim vecinii: Sus, Jos, Stanga, Dreapta (Fara diagonale pentru simplitate)
            neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                cost = 1.0  # Costul miscarii

                # Verificam daca vecinul e in harta si nu e zid
                if 0 <= neighbor[0] < self.width and 0 <= neighbor[1] < self.height:
                    if self.grid[neighbor[1]][neighbor[0]] == 1: continue

                    tentative_g_score = g_score[current] + cost

                    # Daca am gasit un drum mai bun catre acest vecin
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal_node)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        print("[PLANNER] Esec. Nu exista drum liber!")
        return []

    def heuristic(self, a, b):
        """ Functia Heuristica (Manhattan Distance) - Estimeaza distanta ramasa """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_path(self, came_from, current):
        """ Merge inapoi din parinte in parinte pentru a recrea lista de pasi """
        path = []
        while current in came_from:
            wx, wy = self.grid_to_world(current[0], current[1])
            path.append((wx, wy))
            current = came_from[current]
        path.reverse()  # Inversam lista ca sa fie Start -> Goal
        return path