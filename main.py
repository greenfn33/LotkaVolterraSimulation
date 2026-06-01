import pygame  # librairie pour l'affichage graphique et les interactions
import random  # pour les valeurs aleatoires (position, vitesse, etc.)
import math  # pour les calculs geometriques (angles, distances)
import matplotlib.pyplot as plt  # pour tracer les graphiques de population a la fin
from matplotlib.backends.backend_agg import FigureCanvasAgg  # convertit matplotlib en image pygame

pygame.init()  # demarre tous les modules pygame

# taille de la fenetre principale
WIDTH = 1400
HEIGHT = 720

screen = pygame.display.set_mode((WIDTH, HEIGHT))  # cree la fenetre
pygame.display.set_caption("Simulation Proies / Predateurs")  # titre de la fenetre

clock = pygame.time.Clock()  # sert a controler le nombre de frames par seconde

# couleurs utilisees dans la simulation
BLACK        = (0, 0, 0)
WHITE        = (255, 255, 255)
GREEN        = (0, 230, 0)
RED          = (230, 0, 0)
PACMAN_YELLOW = (255, 216, 0)  # couleur du predateur
FOOD_RED     = (220, 40, 40)   # baie
FOOD_ORANGE  = (240, 140, 20)  # carotte
FOOD_GREEN   = (40, 160, 60)   # graine

# taille des agents sur l'ecran
RADIUS       = 11
DIAMETER     = RADIUS * 2  # utilise pour les collisions

# nombre d'agents au debut de la simulation
PREY_INIT      = 80
PREDATOR_INIT  = 12

# energie de depart de chaque agent, choisie au hasard dans cet intervalle
ENERGY_INIT_MIN = 60
ENERGY_INIT_MAX = 120

# energie perdue a chaque tick selon le type d'agent
ENERGY_COST_PREY      = 0.02   # les proies depensent peu
ENERGY_COST_PREDATOR  = 0.14   # les predateurs depensent plus (cout de la chasse)

# energie gagnee en mangeant
ENERGY_FROM_RESOURCE = 18  # proie qui touche une ressource
ENERGY_FROM_PREY     = 25  # predateur qui attrape une proie

# seuil et cout de la reproduction
REPRO_THRESHOLD = 140  # energie minimale pour pouvoir se reproduire
REPRO_COST      = 55   # energie retiree au parent apres la reproduction

# plage de vitesse des proies
PREY_SPEED_MIN = 2.6
PREY_SPEED_MAX = 4.2

# plage de vitesse des predateurs (plus rapides que les proies)
PRED_SPEED_MIN = 3.4
PRED_SPEED_MAX = 6.0

# distances pour detecter les collisions
COLLISION_DIST       = DIAMETER               # distance de contact entre deux agents
PREDATION_DIST_MULT  = 0.9                    # facteur ajustant la portee de la predation
PREDATION_DIST       = DIAMETER * PREDATION_DIST_MULT  # distance reelle pour attraper une proie

# parametres des ressources (nourriture) dans l'environnement
RESOURCE_RADIUS    = 6     # taille visuelle de la nourriture
RESOURCE_MAX       = 30    # quantite initiale d'une ressource quand elle apparait
NB_RESOURCES       = 260   # nombre total de slots de ressources dans la simulation
RESOURCE_SPAWN_PROB = 0.015  # probabilite qu'une ressource vide reapparaisse a chaque tick

# vitesse globale de la simulation (modifiable en jeu avec les fleches)
SIM_SPEED = 0.8  # valeur de depart

# mode turbo pour passer la simulation plus vite sans tout afficher
FAST_FORWARD = False          # desactive par defaut
FAST_FORWARD_SKIP = 10        # nombre de ticks calcules pour chaque frame affichee
MAX_FPS_IN_FAST_MODE = 120    # limite de fps en mode turbo

# plafond doux pour eviter une explosion infinie de la population
PREY_CAP      = 400
PREDATOR_CAP  = 140

# reinsertion automatique si une population tombe trop bas
PREY_MIN_REINFORCE     = 15   # seuil de proies avant reinsertion
PREY_REINFORCE_COUNT   = 6    # nombre de proies rajoutees
PRED_MIN_REINFORCE     = 4    # seuil de predateurs avant reinsertion
PRED_REINFORCE_COUNT   = 8    # nombre de predateurs rajoutes

# taille d'une cellule dans la grille spatiale (optimisation des collisions)
CELL_SIZE = max(1, DIAMETER * 2)

# parametres du dessin du fond foret
CANOPY_HEIGHT = 240   # hauteur de la canopee en haut de l'ecran
CANOPY_SEED   = 7     # graine fixe pour que le fond soit toujours le meme


def build_forest_canopy(width, height, canopy_height):
    # cree le fond d'ecran qui imite une foret vue de dessus
    surface = pygame.Surface((width, height))

    # gradient de couleur vertical du bas vers le haut pour simuler la profondeur
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(6  + 10 * (1 - t))
        g = int(20 + 22 * (1 - t))
        b = int(8  + 12 * (1 - t))
        pygame.draw.line(surface, (r, g, b), (0, y), (width, y))  # dessine chaque ligne horizontale

    rng = random.Random(CANOPY_SEED)  # generateur fixe pour un rendu constant

    # trois couches d'arbres a differentes hauteurs et tailles
    layers = [
        (canopy_height * 0.55, 34, 60, (28, 60, 24)),   # couche basse, gros arbres sombres
        (canopy_height * 0.40, 28, 50, (36, 90, 34)),   # couche du milieu
        (canopy_height * 0.25, 22, 40, (46, 120, 42)),  # couche haute, petits arbres clairs
    ]
    for y_base, rmin, rmax, base_col in layers:
        count = int(width / 12)  # nombre d'arbres dans cette couche
        for _ in range(count):
            x   = rng.randint(-20, width + 20)  # position x aleatoire (peut depasser les bords)
            y   = rng.randint(0, int(y_base))    # position y dans la zone de la couche
            rad = rng.randint(rmin, rmax)         # rayon de l'arbre
            j   = rng.randint(-8, 8)              # petite variation de couleur pour le realisme
            col = (min(255, base_col[0] + j), min(255, base_col[1] + j), min(255, base_col[2] + j))
            pygame.draw.circle(surface, col, (x, y), rad)  # dessine un arbre comme un cercle

    # patch semi-transparent sombre en haut pour renforcer la canopee
    top_patch = pygame.Surface((width, int(canopy_height * 0.45)))
    top_patch.fill((20, 50, 22))
    top_patch.set_alpha(120)  # transparence partielle
    surface.blit(top_patch, (0, 0))

    # sentiers dans la foret
    path_color = (70, 85, 60)
    for offset in (int(width * 0.25), int(width * 0.65), int(width * 0.85)):
        points = [
            (offset,      canopy_height - 10),    # debut du sentier
            (offset - 40, canopy_height + 80),
            (offset + 20, canopy_height + 200),
            (offset - 30, height - 20),            # fin du sentier en bas
        ]
        pygame.draw.lines(surface, path_color, False, points, 24)  # trace le sentier en courbe

    # riviere qui traverse l'ecran en forme de sinus
    river_color  = (40, 90, 120)
    river_points = []
    for x in range(-50, width + 51, 80):
        y = int(height * 0.55 + math.sin(x * 0.02) * 25)  # ondulation horizontale
        river_points.append((x, y))
    pygame.draw.lines(surface, river_color, False, river_points, 30)  # trace la riviere

    # rochers decoratifs places a des positions fixes
    rock_color = (95, 95, 95)
    pygame.draw.ellipse(surface, rock_color, (int(width * 0.12), int(height * 0.72), 70, 40))
    pygame.draw.ellipse(surface, rock_color, (int(width * 0.78), int(height * 0.58), 60, 32))
    pygame.draw.ellipse(surface, rock_color, (int(width * 0.32), int(height * 0.64), 55, 30))
    pygame.draw.ellipse(surface, rock_color, (int(width * 0.55), int(height * 0.46), 65, 34))
    pygame.draw.ellipse(surface, rock_color, (int(width * 0.88), int(height * 0.70), 50, 28))
    return surface  # retourne la surface avec tout le fond dessine


def draw_pacman(surface, x, y, radius, direction, mouth_open):
    # dessine un predateur en forme de pacman avec une bouche qui bouge
    pygame.draw.circle(surface, PACMAN_YELLOW, (int(x), int(y)), radius)  # corps jaune

    # calcul de l'ouverture de la bouche selon la direction de deplacement
    mouth_angle = math.radians(10 + 40 * mouth_open)  # angle de la bouche (s'ouvre et se ferme)
    a1 = direction - mouth_angle / 2  # bord superieur de la bouche
    a2 = direction + mouth_angle / 2  # bord inferieur de la bouche
    p1 = (x + math.cos(a1) * radius, y + math.sin(a1) * radius)
    p2 = (x + math.cos(a2) * radius, y + math.sin(a2) * radius)
    pygame.draw.polygon(surface, BLACK, [(x, y), p1, p2])  # triangle noir = la bouche

    # oeil du predateur, positionne par rapport a la direction
    eye_angle = direction - math.radians(55)
    eye_r = max(2, int(radius * 0.12))  # taille de l'oeil proportionnelle au rayon
    eye_x = x + math.cos(eye_angle) * radius * 0.45
    eye_y = y + math.sin(eye_angle) * radius * 0.45
    pygame.draw.circle(surface, BLACK, (int(eye_x), int(eye_y)), eye_r)  # point noir = oeil


def draw_mini_graph(surface, rect, hist_prey, hist_pred):
    # dessine le petit graphique de population dans le coin de l'ecran
    pygame.draw.rect(surface, (20, 20, 20), rect, border_radius=8)   # fond sombre
    pygame.draw.rect(surface, (80, 80, 80), rect, 2, border_radius=8)  # bordure grise

    if len(hist_prey) < 2:  # pas assez de donnees pour tracer une ligne
        return

    # on garde seulement les derniers points qui rentrent dans la largeur du graphique
    max_points = rect.width - 20
    start     = max(0, len(hist_prey) - max_points)
    data_prey = hist_prey[start:]
    data_pred = hist_pred[start:]
    max_val   = max(1, max(data_prey + data_pred))  # valeur max pour normaliser

    x0, y0    = rect.x + 10, rect.y + 10  # coin superieur gauche de la zone de trace
    w, h      = rect.width - 20, rect.height - 20

    def map_point(i, v):
        # convertit un index et une valeur en coordonnees pixel dans le graphique
        x = x0 + int(i * (w / max(1, len(data_prey) - 1)))
        y = y0 + int(h - (v / max_val) * h)
        return (x, y)

    prey_pts = [map_point(i, v) for i, v in enumerate(data_prey)]  # points des proies
    pred_pts = [map_point(i, v) for i, v in enumerate(data_pred)]  # points des predateurs

    if len(prey_pts) > 1:
        pygame.draw.lines(surface, (230, 0, 0),   False, prey_pts, 2)  # courbe rouge = proies
    if len(pred_pts) > 1:
        pygame.draw.lines(surface, (255, 210, 0), False, pred_pts, 2)  # courbe jaune = predateurs


def draw_legend(surface, x, y, font, blur_alpha=160):
    # dessine la legende qui explique les symboles de la simulation
    legend_w, legend_h = 220, 110
    legend_surf = pygame.Surface((legend_w, legend_h), pygame.SRCALPHA)
    legend_surf.fill((30, 30, 30, blur_alpha))  # fond semi-transparent
    surface.blit(legend_surf, (x, y))
    pygame.draw.rect(surface, (90, 90, 90), (x, y, legend_w, legend_h), 2)  # bordure

    # icone et label du predateur
    draw_pacman(surface, x + 20, y + 25, 10, 0, 0.6)
    surface.blit(font.render("Predateur", True, (240, 240, 240)), (x + 40, y + 16))

    # icone et label de la proie
    pygame.draw.circle(surface, (230, 0, 0), (x + 20, y + 55), 10)
    surface.blit(font.render("Proie", True, (240, 240, 240)), (x + 40, y + 46))

    # icone et label de la nourriture (deux lignes = feuille stylisee)
    pygame.draw.line(surface, FOOD_GREEN, (x + 20, y + 80), (x + 20, y + 65), 2)
    pygame.draw.line(surface, FOOD_GREEN, (x + 20, y + 75), (x + 14, y + 69), 2)
    surface.blit(font.render("Nourriture", True, (240, 240, 240)), (x + 40, y + 70))


def draw_speed_ui(surface, x, y, font, bold_font):
    # affiche la vitesse de simulation courante et les touches pour la modifier
    label = bold_font.render("SIM_SPEED", True, (255, 255, 255))
    surface.blit(label, (x, y))
    val = font.render(f"{SIM_SPEED:.2f}  (</>)", True, (220, 220, 220))  # valeur et rappel des touches
    surface.blit(val, (x, y + 20))


def draw_end_button(surface, font):
    # affiche le bouton "terminer" en bas de l'ecran pendant la simulation
    btn_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 50, 200, 36)
    pygame.draw.rect(surface, (180, 40, 40), btn_rect, border_radius=8)    # fond rouge
    pygame.draw.rect(surface, (220, 100, 100), btn_rect, 2, border_radius=8)  # bordure claire
    label = font.render("Terminer", True, WHITE)
    surface.blit(label, (btn_rect.centerx - label.get_width() // 2,
                         btn_rect.centery - label.get_height() // 2))
    return btn_rect  # retourne le rectangle pour detecter les clics


def pick_emoji_font(size):
    """Try to find a color-emoji capable font; return None if unavailable."""
    # essaie de trouver une police qui supporte les emojis de couleur
    for name in ("Apple Color Emoji", "Noto Color Emoji", "Segoe UI Emoji"):
        try:
            f = pygame.font.SysFont(name, size)
            if f:
                return f
        except Exception:
            continue
    return None  # retourne none si aucune police emoji n'est disponible


def draw_food(surface, x, y, kind, emoji_font):
    # dessine une ressource alimentaire, en emoji si possible sinon en formes geometriques
    drawn_emoji = False
    if emoji_font is not None:
        try:
            # choix de l'emoji selon le type de nourriture
            emoji = "🍓" if kind == "berry" else ("🥕" if kind == "carrot" else "🌱")
            img = emoji_font.render(emoji, True, WHITE)
            surface.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)))  # centre l'emoji
            drawn_emoji = True
        except Exception:
            pass  # silently fall back; no permanent global flag needed

    if not drawn_emoji:
        # fallback: formes simples si les emojis ne fonctionnent pas
        if kind == "berry":
            pygame.draw.circle(surface, FOOD_RED, (int(x), int(y)), RESOURCE_RADIUS)  # baie = cercle rouge
            pygame.draw.circle(surface, FOOD_GREEN, (int(x), int(y - RESOURCE_RADIUS // 2)), max(2, RESOURCE_RADIUS // 3))  # petite feuille verte
        elif kind == "carrot":
            r = RESOURCE_RADIUS
            pygame.draw.polygon(surface, FOOD_ORANGE, [(x, y + r), (x - r, y - r), (x + r, y - r)])  # triangle = carotte
            pygame.draw.line(surface, FOOD_GREEN, (int(x), int(y - r)), (int(x), int(y - r - 4)), 2)  # tige verte
        else:  # seed
            # graine = deux lignes vertes en croix partielle
            pygame.draw.line(surface, FOOD_GREEN, (int(x), int(y + RESOURCE_RADIUS)), (int(x), int(y - RESOURCE_RADIUS)), 2)
            pygame.draw.line(surface, FOOD_GREEN, (int(x), int(y)), (int(x - 4), int(y - 4)), 2)


# variables globales de l'interface parametres
show_ui    = False   # masque ou affiche la liste des parametres en cours de simulation
param_index = 0      # quel parametre est actuellement selectionne dans la liste

# liste de tous les parametres modifiables avec leur pas de modification et leurs limites
PARAM_LIST = [
    ("PREY_INIT",           1,     0,    500),
    ("PREDATOR_INIT",       1,     0,    500),
    ("ENERGY_INIT_MIN",     1,     0,    999),
    ("ENERGY_INIT_MAX",     1,     0,    999),
    ("ENERGY_COST_PREY",    0.01,  0.0,  5.0),
    ("ENERGY_COST_PREDATOR",0.01,  0.0,  5.0),
    ("ENERGY_FROM_RESOURCE",1,     0,    999),
    ("ENERGY_FROM_PREY",    1,     0,    999),
    ("REPRO_THRESHOLD",     1,     0,    999),
    ("REPRO_COST",          1,     0,    999),
    ("PREY_SPEED_MIN",      0.1,   0.0,  20.0),
    ("PREY_SPEED_MAX",      0.1,   0.0,  20.0),
    ("PRED_SPEED_MIN",      0.1,   0.0,  20.0),
    ("PRED_SPEED_MAX",      0.1,   0.0,  20.0),
    ("RADIUS",              1,     1,    50),
    ("PREDATION_DIST_MULT", 0.05,  0.1,  2.0),
    ("RESOURCE_RADIUS",     1,     1,    50),
    ("RESOURCE_MAX",        1,     0,    999),
    ("NB_RESOURCES",        1,     0,    1000),
    ("RESOURCE_SPAWN_PROB", 0.01,  0.0,  1.0),
    ("PREY_CAP",            10,    10,   2000),
    ("PREDATOR_CAP",        5,     3,    500),
    ("PREY_MIN_REINFORCE",  1,     0,    100),
    ("PREY_REINFORCE_COUNT",1,     0,    50),
    ("PRED_MIN_REINFORCE",  1,     0,    50),
    ("PRED_REINFORCE_COUNT",1,     0,    20),
]

_PARAMS = {name: True for name, *_ in PARAM_LIST}  # ensemble des noms valides pour get/set

# categories en francais pour chaque parametre, affichees dans l'interface
PARAM_FR_TITLES = {
    "PREY_INIT": "Population",
    "PREDATOR_INIT": "Population",
    "ENERGY_INIT_MIN": "Energie",
    "ENERGY_INIT_MAX": "Energie",
    "ENERGY_COST_PREY": "Energie",
    "ENERGY_COST_PREDATOR": "Energie",
    "ENERGY_FROM_RESOURCE": "Energie",
    "ENERGY_FROM_PREY": "Energie",
    "REPRO_THRESHOLD": "Reproduction",
    "REPRO_COST": "Reproduction",
    "PREY_SPEED_MIN": "Vitesse",
    "PREY_SPEED_MAX": "Vitesse",
    "PRED_SPEED_MIN": "Vitesse",
    "PRED_SPEED_MAX": "Vitesse",
    "RADIUS": "Taille",
    "PREDATION_DIST_MULT": "Predation",
    "RESOURCE_RADIUS": "Ressource",
    "RESOURCE_MAX": "Ressource",
    "NB_RESOURCES": "Ressource",
    "RESOURCE_SPAWN_PROB": "Ressource",
    "PREY_CAP": "Limite population",
    "PREDATOR_CAP": "Limite population",
    "PREY_MIN_REINFORCE": "Anti-extinction",
    "PREY_REINFORCE_COUNT": "Anti-extinction",
    "PRED_MIN_REINFORCE": "Anti-extinction",
    "PRED_REINFORCE_COUNT": "Anti-extinction",
}


def get_param(name):
    # lit la valeur courante d'un parametre global par son nom
    return globals()[name]


def set_param(name, value):
    # modifie un parametre global et recalcule les valeurs derivees si necessaire
    global DIAMETER, COLLISION_DIST, PREDATION_DIST, CELL_SIZE
    if name not in _PARAMS:
        return
    cur = globals()[name]
    if isinstance(cur, int):
        value = int(round(value))   # garde le type entier si necessaire
    else:
        value = round(float(value), 4)  # arrondit les flottants
    globals()[name] = value

    # recompute derived
    if name in ("RADIUS", "PREDATION_DIST_MULT"):
        # si le rayon change, tout ce qui depend du diametre doit etre recalcule
        DIAMETER        = RADIUS * 2
        COLLISION_DIST  = DIAMETER
        PREDATION_DIST  = DIAMETER * PREDATION_DIST_MULT
        CELL_SIZE       = max(1, DIAMETER * 2)


def adjust_param(name, delta):
    # augmente ou diminue un parametre d'un pas defini dans PARAM_LIST
    for n, step, vmin, vmax in PARAM_LIST:
        if n == name:
            new_val = get_param(n) + delta      # applique le delta
            new_val = max(vmin, min(vmax, new_val))  # reste dans les limites
            set_param(n, new_val)
            return


def draw_param_ui(surface, font):
    # affiche la liste des parametres en jeu si le mode ui est actif (touche h)
    if not show_ui:
        return
    x, y = 10, 80
    for i, (n, _, _, _) in enumerate(PARAM_LIST):
        val   = get_param(n)
        color = (255, 255, 0) if i == param_index else (180, 180, 180)  # jaune = selectionne
        cat = PARAM_FR_TITLES.get(n, "Parametre")
        txt   = font.render(f"[{cat}] {n}: {val}", True, color)
        surface.blit(txt, (x, y))
        y += 18  # espace entre chaque ligne de parametre


# definition des classes (programmation orientee objet)

class Organism:
    __slots__ = ("is_prey", "x", "y", "vx", "vy", "speed", "energy", "eat_cooldown")
    # slots limite les attributs possibles pour une meilleure performance memoire

    def __init__(self, is_prey, x, y, vx, vy, speed, energy):
        # initialise un organisme avec tous ses attributs de base
        self.is_prey      = is_prey   # vrai si c'est une proie, faux si predateur
        self.x            = x         # position horizontale
        self.y            = y         # position verticale
        self.vx           = vx        # vitesse en x
        self.vy           = vy        # vitesse en y
        self.speed        = speed     # norme de la vitesse (scalaire)
        self.energy       = energy    # reserve d'energie courante
        self.eat_cooldown = 0         # delai apres avoir mange avant de pouvoir manger encore

    def move(self):
        # deplace l'organisme et le fait rebondir sur les bords de la fenetre
        self.x += self.vx
        self.y += self.vy
        if self.x < RADIUS:  # bord gauche
            self.x  = RADIUS
            self.vx = abs(self.vx)  # inverse la direction horizontale
        elif self.x > WIDTH - RADIUS:  # bord droit
            self.x  = WIDTH - RADIUS
            self.vx = -abs(self.vx)
        if self.y < RADIUS:  # bord haut
            self.y  = RADIUS
            self.vy = abs(self.vy)  # inverse la direction verticale
        elif self.y > HEIGHT - RADIUS:  # bord bas
            self.y  = HEIGHT - RADIUS
            self.vy = -abs(self.vy)

    def energy_cost(self):
        # retire de l'energie a chaque tick selon le type et la vitesse de l'organisme
        if self.is_prey:
            self.energy -= ENERGY_COST_PREY * (1 + self.speed * 0.1)      # proie: cout faible
        else:
            self.energy -= ENERGY_COST_PREDATOR * (1 + self.speed * 0.15) # predateur: cout eleve

    def can_reproduce(self, pop_count):
        """Reproduction blocked when population is at or above its soft cap."""
        # verifie si l'organisme a assez d'energie et si la population n'est pas au plafond
        cap = PREY_CAP if self.is_prey else PREDATOR_CAP
        return self.energy >= REPRO_THRESHOLD and pop_count < cap

    def reproduce(self):
        # cree un nouvel organisme enfant pres du parent avec une direction aleatoire
        angle = random.uniform(0, 2 * math.pi)  # direction de naissance aleatoire
        if self.is_prey:
            speed = random.uniform(PREY_SPEED_MIN, PREY_SPEED_MAX)  # vitesse de l'enfant proie
        else:
            speed = random.uniform(PRED_SPEED_MIN, PRED_SPEED_MAX)  # vitesse de l'enfant predateur
        vx = math.cos(angle) * speed  # composante x de la vitesse
        vy = math.sin(angle) * speed  # composante y de la vitesse
        child_x = self.x + math.cos(angle) * (DIAMETER + 4)  # apparait juste a cote du parent
        child_y = self.y + math.sin(angle) * (DIAMETER + 4)
        child_energy = self.energy * 0.5  # l'enfant recoit la moitie de l'energie du parent
        self.energy -= REPRO_COST         # le parent perd aussi de l'energie
        return Organism(self.is_prey, child_x, child_y, vx, vy, speed, child_energy)


class Resource:
    __slots__ = ("x", "y", "amount", "kind")  # slots pour la performance

    def __init__(self):
        # resource commence vide, elle va apparaitre plus tard via spawn()
        self.x      = 0
        self.y      = 0
        self.amount = 0
        self.kind   = "seed"  # type par defaut

    def spawn(self):
        # fait reapparaitre la ressource a une position aleatoire si elle est epuisee
        if self.amount <= 0 and random.random() < RESOURCE_SPAWN_PROB:
            self.x      = random.randint(20, WIDTH - 20)   # position x aleatoire dans la fenetre
            self.y      = random.randint(20, HEIGHT - 20)  # position y aleatoire dans la fenetre
            self.amount = RESOURCE_MAX                      # recharge la quantite
            self.kind   = random.choice(["berry", "carrot", "seed"])  # type aleatoire


def create_random(is_prey):
    # cree un organisme place aleatoirement dans la fenetre avec des attributs aleatoires
    x     = random.uniform(RADIUS, WIDTH  - RADIUS)  # x dans les limites de la fenetre
    y     = random.uniform(RADIUS, HEIGHT - RADIUS)  # y dans les limites de la fenetre
    speed = random.uniform(PREY_SPEED_MIN, PREY_SPEED_MAX) if is_prey \
            else random.uniform(PRED_SPEED_MIN, PRED_SPEED_MAX)  # vitesse selon le type
    angle = random.uniform(0, 2 * math.pi)  # direction aleatoire
    vx    = math.cos(angle) * speed  # vitesse horizontale
    vy    = math.sin(angle) * speed  # vitesse verticale
    energy = random.uniform(ENERGY_INIT_MIN, ENERGY_INIT_MAX)  # energie de depart aleatoire
    return Organism(is_prey, x, y, vx, vy, speed, energy)


# grille spatiale pour optimiser la detection des collisions

def build_grid(organisms, cell_size):
    # divise l'espace en cellules et associe chaque organisme a sa cellule
    grid = {}
    for idx, o in enumerate(organisms):
        col = int(o.x / cell_size)  # colonne de la cellule
        row = int(o.y / cell_size)  # ligne de la cellule
        grid.setdefault((col, row), []).append(idx)  # ajoute l'index a la cellule
    return grid


def nearby_indices(grid, o, cell_size, radius_cells=1):
    # retourne les indices des organismes dans les cellules voisines
    col = int(o.x / cell_size)
    row = int(o.y / cell_size)
    for dc in range(-radius_cells, radius_cells + 1):   # boucle sur les colonnes voisines
        for dr in range(-radius_cells, radius_cells + 1):  # boucle sur les lignes voisines
            for idx in grid.get((col + dc, row + dr), ()):
                yield idx  # retourne chaque voisin un par un


# gestion des collisions entre organismes

def elastic_collision(a, b):
    # applique une collision elastique entre deux organismes de meme masse
    dx = b.x - a.x
    dy = b.y - a.y
    dist = math.hypot(dx, dy)  # distance reelle entre les deux
    if dist == 0 or dist > COLLISION_DIST:
        return  # pas de collision si trop loin ou superposition exacte

    nx = dx / dist  # vecteur normal unitaire entre les deux
    ny = dy / dist
    dvx = a.vx - b.vx  # difference de vitesse
    dvy = a.vy - b.vy
    vn  = dvx * nx + dvy * ny  # composante normale de la vitesse relative
    if vn > 0:
        return  # ils s'eloignent deja, pas besoin de rien faire

    impulse = -vn          # equal mass -> impulse = -vn (factor of 2 cancels)
    a.vx += impulse * nx   # applique l'impulsion a l'organisme a
    a.vy += impulse * ny
    b.vx -= impulse * nx   # impulsion opposee sur l'organisme b
    b.vy -= impulse * ny

    # separation pour eviter qu'ils restent superposes
    overlap = COLLISION_DIST - dist
    a.x -= nx * overlap / 2  # pousse a en arriere
    a.y -= ny * overlap / 2
    b.x += nx * overlap / 2  # pousse b en avant
    b.y += ny * overlap / 2


def resolve_collisions(organisms, cell_size):
    # parcourt tous les organismes et applique les collisions entre voisins
    grid = build_grid(organisms, cell_size)  # construit la grille a chaque tick
    checked = set()  # garde en memoire les paires deja traitees
    for idx, o in enumerate(organisms):
        for jdx in nearby_indices(grid, o, cell_size, radius_cells=1):
            if jdx <= idx:
                continue  # evite les doublons (on ne traite chaque paire qu'une fois)
            key = (idx, jdx)
            if key in checked:
                continue
            checked.add(key)
            elastic_collision(o, organisms[jdx])  # applique la collision


# gestion de la predation

def resolve_predation(predators, prey):
    # chaque predateur cherche la proie la plus proche dans sa zone et la mange
    if not prey:
        return prey  # aucune proie disponible

    prey_grid = build_grid(prey, CELL_SIZE)  # grille des proies pour recherche rapide
    eaten     = set()  # indices des proies deja mangees ce tick

    for pred in predators:
        col = int(pred.x / CELL_SIZE)
        row = int(pred.y / CELL_SIZE)
        best_idx  = -1
        best_dist = float("inf")

        # regarde dans un rayon de 2 cellules autour du predateur
        for dc in range(-2, 3):
            for dr in range(-2, 3):
                for idx in prey_grid.get((col + dc, row + dr), ()):
                    if idx in eaten:
                        continue  # cette proie est deja mangee
                    pr = prey[idx]
                    d  = math.hypot(pr.x - pred.x, pr.y - pred.y)
                    if d < PREDATION_DIST and d < best_dist:
                        best_dist = d    # garde la proie la plus proche
                        best_idx  = idx

        if best_idx != -1:
            eaten.add(best_idx)          # marque la proie comme mangee
            pred.energy       += ENERGY_FROM_PREY  # le predateur gagne de l'energie
            pred.eat_cooldown  = 6       # petit delai avant de pouvoir remanger

    return [p for i, p in enumerate(prey) if i not in eaten]  # retourne les proies survivantes


# gestion de la consommation de nourriture par les proies

def resolve_resources(prey, resources):
    """Prey eat food items; uses a simple sweep (resources are sparse)."""
    contact_dist = RESOURCE_RADIUS + RADIUS  # distance de contact proie-ressource
    for res in resources:
        if res.amount <= 0:
            continue  # ressource deja consommee
        for pr in prey:
            if math.hypot(pr.x - res.x, pr.y - res.y) < contact_dist:
                pr.energy += ENERGY_FROM_RESOURCE  # la proie gagne de l'energie
                res.amount = 0                     # la ressource est consommee
                break  # une seule proie mange la ressource


# reinsertion automatique pour eviter l'extinction totale

def maybe_reinforce(prey, predators):
    # si une population tombe trop bas, on rajoute quelques individus
    if len(prey) < PREY_MIN_REINFORCE:
        for _ in range(PREY_REINFORCE_COUNT):
            prey.append(create_random(True))  # rajoute des proies

    if len(predators) < PRED_MIN_REINFORCE:
        for _ in range(PRED_REINFORCE_COUNT):
            predators.append(create_random(False))  # rajoute des predateurs

    return prey, predators


# creation initiale de tous les organismes et ressources

prey      = [create_random(True)  for _ in range(PREY_INIT)]     # liste des proies
predators = [create_random(False) for _ in range(PREDATOR_INIT)] # liste des predateurs
resources = [Resource()           for _ in range(NB_RESOURCES)]  # liste des ressources

# historique des populations pour le graphique final
history_prey = []
history_pred = []
history_time = []
t = 0  # compteur de ticks

# polices de texte pour l'affichage
font      = pygame.font.Font(None, 32)
bold_font = pygame.font.Font(None, 28)
bold_font.set_bold(True)

# generation du fond d'ecran foret et chargement de la police emoji
background_surface = build_forest_canopy(WIDTH, HEIGHT, CANOPY_HEIGHT)
emoji_font         = pick_emoji_font(max(18, int(RESOURCE_RADIUS * 3)))

# polices pour la page titre et la page de configuration
title_font = pygame.font.Font(None, 72)    # grand texte pour le titre principal
subtitle_font = pygame.font.Font(None, 38) # texte moyen pour les sous-titres

# variables d'etat pour l'interface de configuration
config_help = True   # affiche l'aide au demarrage
editing = False      # indique si l'utilisateur est en train de taper une valeur
edit_name = ""       # nom du parametre en cours d'edition
edit_buffer = ""     # texte tape par l'utilisateur


def draw_title_page(surface):
    # Page titre du projet
    surface.blit(background_surface, (0, 0))  # fond foret
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 95))  # voile noir semi-transparent pour lisibilite du texte
    surface.blit(overlay, (0, 0))

    # textes de la page titre
    title_text = title_font.render("Simulation Proies / Predateurs", True, WHITE)
    but_text = subtitle_font.render("Le but :", True, (232, 232, 210))
    point_1 = font.render("- Observer l'evolution des proies et des predateurs", True, (232, 232, 210))
    point_2 = font.render("- Comparer la simulation avec la theorie Lotka-Volterra", True, (232, 232, 210))
    point_3 = font.render("- Tester l'effet des parametres sur l'equilibre du systeme", True, (232, 232, 210))
    enter_text = font.render("Appuie sur ENTREE pour aller aux parametres", True, WHITE)

    # centre tous les textes horizontalement
    surface.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 220))
    surface.blit(but_text, (WIDTH // 2 - but_text.get_width() // 2, 300))
    surface.blit(point_1, (WIDTH // 2 - point_1.get_width() // 2, 342))
    surface.blit(point_2, (WIDTH // 2 - point_2.get_width() // 2, 375))
    surface.blit(point_3, (WIDTH // 2 - point_3.get_width() // 2, 408))
    surface.blit(enter_text, (WIDTH // 2 - enter_text.get_width() // 2, 458))


def draw_config_ui(surface, font):
    # Page parametres avec petite aide
    surface.fill(BLACK)  # fond noir
    surface.blit(font.render("Parametres de la simulation (FR)", True, WHITE), (10, 10))
    surface.blit(font.render("Note: valeurs par defaut = les plus optimales.", True, (190, 220, 190)), (10, 38))
    surface.blit(font.render("Systeme d'anti-extinction en place: pas de disparition totale.", True, (190, 220, 190)), (10, 60))

    if config_help:
        # instructions de navigation affichees si l'aide est visible
        surface.blit(font.render("UP/DOWN: choisir param   +/-: modifier (pas fin)   E/T: saisir valeur", True, (200, 200, 200)), (10, 88))
        surface.blit(font.render("ENTREE: demarrer   H: aide   LEFT/RIGHT: SIM_SPEED", True, (200, 200, 200)), (10, 110))

    x, y = 10, 145  # position de depart de la liste des parametres
    for i, (n, _, _, _) in enumerate(PARAM_LIST):
        val = get_param(n)
        if editing and n == edit_name:
            # parametre en cours d'edition: couleur orange et curseur _
            color = (255, 200, 120)
            cat = PARAM_FR_TITLES.get(n, "Parametre")
            label = f"[{cat}] {n}: {edit_buffer}_"
        else:
            color = (255, 255, 0) if i == param_index else (220, 220, 220)  # jaune si selectionne
            cat = PARAM_FR_TITLES.get(n, "Parametre")
            label = f"[{cat}] {n}: {val}"
        surface.blit(font.render(label, True, color), (x, y))
        y += 20  # espace entre chaque ligne

    # legende et vitesse affiches aussi sur cette page
    draw_legend(surface, WIDTH - 240, 10, font, blur_alpha=140)
    draw_speed_ui(surface, WIDTH - 240, 130, font, bold_font)


def reset_simulation_state():
    # remet toute la simulation a zero avec les parametres actuels
    global CELL_SIZE, prey, predators, resources, t, show_ui, emoji_font, FAST_FORWARD

    CELL_SIZE = max(1, DIAMETER * 2)  # recalcule la taille des cellules
    prey = [create_random(True) for _ in range(PREY_INIT)]        # regenre les proies
    predators = [create_random(False) for _ in range(PREDATOR_INIT)]  # regenere les predateurs
    resources = [Resource() for _ in range(NB_RESOURCES)]         # regenere les ressources
    history_prey.clear()   # efface l'historique des proies
    history_pred.clear()   # efface l'historique des predateurs
    history_time.clear()   # efface l'historique du temps
    t = 0                  # remet le compteur a zero
    show_ui = False        # cache l'ui des parametres
    FAST_FORWARD = False   # desactive le mode turbo
    emoji_font = pick_emoji_font(max(18, int(RESOURCE_RADIUS * 3)))  # recharge la police emoji


# fonctions pour le graphique de fin de simulation

def _smooth(data, window):
    # lisse une serie de donnees avec une moyenne glissante pour reduire le bruit
    if window <= 1 or len(data) < window:
        return list(data)  # rien a lisser
    result = []
    half = window // 2
    n = len(data)
    for i in range(n):
        lo = max(0, i - half)         # borne gauche de la fenetre
        hi = min(n, i + half + 1)     # borne droite de la fenetre
        result.append(sum(data[lo:hi]) / (hi - lo))  # moyenne locale
    return result


def _detect_period(signal, times):
    # estime la periode des oscillations en comptant les passages a la moyenne
    if len(signal) < 20:
        return None  # pas assez de donnees
    mean = sum(signal) / len(signal)
    centered = [v - mean for v in signal]  # centre le signal autour de zero
    crossings = []
    for i in range(1, len(centered)):
        if centered[i - 1] < 0 <= centered[i]:  # passage par zero vers le haut
            frac = -centered[i - 1] / max(1e-9, centered[i] - centered[i - 1])
            crossings.append(times[i - 1] + frac * (times[i] - times[i - 1]))  # interpolation
    if len(crossings) < 3:
        return None  # pas assez de cycles detectes
    gaps = [crossings[k + 1] - crossings[k] for k in range(len(crossings) - 1)]  # duree de chaque cycle
    return sum(gaps) / len(gaps)  # periode moyenne


def fit_lv_from_history(history_prey, history_pred, history_time):
    # estime les parametres de lotka-volterra a partir des donnees de la simulation
    n = len(history_prey)
    skip = max(1, n // 10)  # ignore les premiers ticks de demarrage

    h_prey = history_prey[skip:]  # donnees sans le debut instable
    h_pred = history_pred[skip:]
    h_time = history_time[skip:]

    x_star = max(1.0, sum(h_prey) / len(h_prey))  # moyenne des proies = equilibre estime
    y_star = max(1.0, sum(h_pred) / len(h_pred))  # moyenne des predateurs = equilibre estime

    amp_prey = max(0.5, (max(h_prey) - min(h_prey)) / 2)  # amplitude des oscillations des proies
    amp_pred = max(0.5, (max(h_pred) - min(h_pred)) / 2)  # amplitude des oscillations des predateurs

    smooth_p = _smooth(h_prey, max(1, len(h_prey) // 80))  # lisse pour mieux detecter la periode
    period_ticks = _detect_period(smooth_p, h_time)
    if period_ticks is None or period_ticks <= 0:
        period_ticks = (history_time[-1] - history_time[0]) / 4.0  # estimation par defaut

    t_norm = 1.0
    ag = (2 * math.pi / t_norm) ** 2  # frequence angulaire au carre
    r = (amp_prey / amp_pred) ** 2 * (x_star / y_star)  # ratio des amplitudes
    r = max(0.1, min(r, 10.0))  # borne le ratio pour eviter des valeurs absurdes

    # calcul des parametres alpha, beta, delta, gamma de lotka-volterra
    gamma = math.sqrt(ag / r)
    alpha = r * gamma
    delta = gamma / x_star
    beta = alpha / y_star

    ticks_per_lv = period_ticks
    return alpha, beta, delta, gamma, ticks_per_lv


def _lv_deriv(x, y, a, b, d, g):
    # equations differentielles de lotka-volterra
    # retourne les derivees dx/dt et dy/dt
    return a * x - b * x * y, d * x * y - g * y


def step_rk4(x, y, a, b, d, g, dt):
    # integre un pas de temps avec la methode runge-kutta d'ordre 4 (plus precis qu'euler)
    k1x, k1y = _lv_deriv(x, y, a, b, d, g)
    k2x, k2y = _lv_deriv(x + dt / 2 * k1x, y + dt / 2 * k1y, a, b, d, g)  # milieu 1
    k3x, k3y = _lv_deriv(x + dt / 2 * k2x, y + dt / 2 * k2y, a, b, d, g)  # milieu 2
    k4x, k4y = _lv_deriv(x + dt * k3x, y + dt * k3y, a, b, d, g)           # fin
    return (
        max(0.0, x + dt / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)),  # moyenne ponderee des pentes
        max(0.0, y + dt / 6 * (k1y + 2 * k2y + 2 * k3y + k4y)),
    )


def simulate_lv(alpha, beta, delta, gamma, ticks_per_lv, t_max_ticks, steps=10000):
    # simule la solution theorique de lotka-volterra sur la meme duree que la simulation
    dt_lv = (t_max_ticks / ticks_per_lv) / steps  # pas de temps normalise

    # conditions initiales legerement decalees de l'equilibre pour avoir des oscillations
    x0 = (gamma / delta) * 1.5
    y0 = (alpha / beta) * 0.7

    xs, ys = [x0], [y0]
    x, y = x0, y0
    for _ in range(steps):
        x, y = step_rk4(x, y, alpha, beta, delta, gamma, dt_lv)  # avance d'un pas
        xs.append(x)
        ys.append(y)
    tick_axis = [i * t_max_ticks / steps for i in range(steps + 1)]  # axe du temps en ticks
    return tick_axis, xs, ys


def build_graph_surface():
    # construit les trois graphiques matplotlib et les retourne comme une surface pygame
    if not history_time:
        return None  # rien a afficher si la simulation n'a pas tourne

    import matplotlib as mpl

    t_max_sim = history_time[-1]  # duree totale de la simulation

    # estime les parametres lv a partir des donnees
    alpha, beta, delta, gamma, ticks_per_lv = fit_lv_from_history(
        history_prey, history_pred, history_time
    )

    # calcule la courbe theorique lv sur la meme duree
    lv_t, lv_prey_raw, lv_pred_raw = simulate_lv(
        alpha, beta, delta, gamma, ticks_per_lv, t_max_sim, steps=10000
    )

    def range_scale(lv_vals, target_vals):
        # reechantillonne les valeurs lv pour qu'elles aient la meme amplitude que la simulation
        lv_min, lv_max = min(lv_vals) * 0.6, max(lv_vals) * 0.6
        tgt_min, tgt_max = min(target_vals) * 0.6, max(target_vals) * 0.6
        lv_rng = max(lv_max - lv_min, 1e-9)
        tgt_rng = tgt_max - tgt_min
        return [tgt_min + (v - lv_min) * tgt_rng / lv_rng for v in lv_vals]

    lv_prey = range_scale(lv_prey_raw, history_prey)  # lv ajuste a l'echelle des proies
    lv_pred = range_scale(lv_pred_raw, history_pred)  # lv ajuste a l'echelle des predateurs

    win = max(1, len(history_prey) // 120)  # taille de la fenetre de lissage
    smooth_prey = _smooth(history_prey, win)  # courbe lissee des proies
    smooth_pred = _smooth(history_pred, win)  # courbe lissee des predateurs

    # style global des graphiques matplotlib
    mpl.rcParams.update({
        "figure.facecolor": "#f9f9f7",
        "axes.facecolor": "#f9f9f7",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#d8d8d8",
        "grid.linewidth": 0.7,
        "grid.linestyle": "--",
        "font.family": "sans-serif",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.framealpha": 0.85,
        "legend.edgecolor": "#cccccc",
        "legend.fontsize": 10,
    })

    prey_color = "#c03a2b"  # rouge fonce pour les proies
    pred_color = "#2980b9"  # bleu pour les predateurs

    fig, axes = plt.subplots(1, 3, figsize=(22, 5))  # trois graphiques cote a cote
    fig.patch.set_facecolor("#f9f9f7")

    # graphique 1 : donnees brutes de la simulation avec lissage
    ax = axes[0]
    ax.plot(history_time, history_prey, color=prey_color, alpha=0.15, linewidth=0.7)  # brut transparent
    ax.plot(history_time, history_pred, color=pred_color, alpha=0.15, linewidth=0.7)
    ax.plot(history_time, smooth_prey, color=prey_color, linewidth=2.0, label="Proies")   # lisse
    ax.plot(history_time, smooth_pred, color=pred_color, linewidth=2.0, label="Predateurs")
    ax.set_title("Simulation agent (experience)", fontweight="bold", pad=10)
    ax.set_xlabel("Temps (ticks)")
    ax.set_ylabel("Population")
    ax.legend(loc="upper right")
    ax.set_xlim(0, t_max_sim)
    ax.set_ylim(bottom=0)

    # graphique 2 : courbe theorique de lotka-volterra
    ax = axes[1]
    ax.plot(lv_t, lv_prey, color=prey_color, linewidth=2.4, label="Proies (LV)")
    ax.plot(lv_t, lv_pred, color=pred_color, linewidth=2.4, label="Predateurs (LV)")
    ax.fill_between(lv_t, lv_prey, alpha=0.08, color=prey_color)  # remplissage leger sous la courbe
    ax.fill_between(lv_t, lv_pred, alpha=0.08, color=pred_color)
    ax.set_title("Equations de Lotka-Volterra (theorique)", fontweight="bold", pad=10)
    ax.set_xlabel("Temps (ticks)")
    ax.set_ylabel("Population")
    ax.legend(loc="upper right")
    ax.set_xlim(0, t_max_sim)
    ax.set_ylim(bottom=0)

    # graphique 3 : superposition experience vs theorie pour comparer directement
    ax = axes[2]
    ax.plot(history_time, smooth_prey, color=prey_color, linewidth=2.2, label="Proies (experience)")
    ax.plot(history_time, smooth_pred, color=pred_color, linewidth=2.2, label="Predateurs (experience)")
    ax.plot(lv_t, lv_prey, color=prey_color, linestyle="--", linewidth=2.0, label="Proies (LV)")  # pointille = theorique
    ax.plot(lv_t, lv_pred, color=pred_color, linestyle="--", linewidth=2.0, label="Predateurs (LV)")
    ax.set_title("Superposition : experience vs theorie", fontweight="bold", pad=10)
    ax.set_xlabel("Temps (ticks)")
    ax.set_ylabel("Population")
    ax.legend(loc="upper right")
    ax.set_xlim(0, t_max_sim)
    ax.set_ylim(bottom=0)

    plt.tight_layout(pad=2.0)  # evite que les graphiques se chevauchent
    canvas = FigureCanvasAgg(fig)  # convertit la figure en image bitmap
    canvas.draw()
    raw = canvas.buffer_rgba()  # recupere les pixels bruts
    w, h = canvas.get_width_height()
    graph_surface = pygame.image.frombuffer(raw, (w, h), "RGBA").convert_alpha()  # surface pygame
    plt.close(fig)  # libere la memoire matplotlib
    return graph_surface


def draw_graph_page(surface, graph_surface):
    # Page graphique dans meme interface
    surface.blit(background_surface, (0, 0))  # fond foret derriere le graphique

    if graph_surface is None:
        txt = font.render("Aucune donnee a afficher.", True, WHITE)  # message si pas de donnees
        surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2))
    else:
        panel_rect = pygame.Rect(20, 20, WIDTH - 40, HEIGHT - 120)
        pygame.draw.rect(surface, (244, 244, 240), panel_rect, border_radius=8)  # fond clair du panneau
        pygame.draw.rect(surface, (130, 130, 130), panel_rect, 2, border_radius=8)  # bordure

        # redimensionne le graphique pour qu'il rentre dans le panneau en gardant les proportions
        src_w, src_h = graph_surface.get_width(), graph_surface.get_height()
        scale = min(panel_rect.width / src_w, panel_rect.height / src_h)
        draw_w = max(1, int(src_w * scale))
        draw_h = max(1, int(src_h * scale))
        scaled_graph = pygame.transform.smoothscale(graph_surface, (draw_w, draw_h))

        # centre le graphique dans le panneau
        draw_x = panel_rect.x + (panel_rect.width - draw_w) // 2
        draw_y = panel_rect.y + (panel_rect.height - draw_h) // 2
        surface.blit(scaled_graph, (draw_x, draw_y))

    # bouton pour revenir aux parametres et relancer une simulation
    btn_rect = pygame.Rect(WIDTH // 2 - 170, HEIGHT - 58, 340, 40)
    pygame.draw.rect(surface, (40, 110, 40), btn_rect, border_radius=8)    # fond vert
    pygame.draw.rect(surface, (180, 225, 180), btn_rect, 2, border_radius=8)  # bordure claire
    label = font.render("Reset vers la page parametres", True, WHITE)
    surface.blit(label, (btn_rect.centerx - label.get_width() // 2,
                         btn_rect.centery - label.get_height() // 2))
    return btn_rect  # retourne le rectangle pour detecter les clics


# etat initial du programme

screen_state = "title"  # commence sur la page titre
running = True           # boucle principale active
frame_counter = 0        # compte les frames pour le mode turbo
end_btn_rect = pygame.Rect(0, 0, 0, 0)    # rectangle du bouton terminer
graph_reset_btn = pygame.Rect(0, 0, 0, 0) # rectangle du bouton reset sur la page graphique
graph_surface = None  # surface du graphique, generee a la fin de la simulation

reset_simulation_state()  # initialise tous les objets de la simulation

# boucle principale du jeu
while running:
    frame_counter += 1

    for event in pygame.event.get():  # traite tous les evenements en attente
        if event.type == pygame.QUIT:
            running = False  # ferme la fenetre

        if screen_state == "title":
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                screen_state = "config"  # entree = aller aux parametres

        elif screen_state == "config":
            if event.type == pygame.KEYDOWN:
                if editing:
                    # l'utilisateur est en train de taper une valeur
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        try:
                            # convertit le texte en nombre et l'applique si valide
                            new_val = float(edit_buffer) if ("." in edit_buffer or "e" in edit_buffer.lower()) else int(edit_buffer)
                            _, _, vmin, vmax = next(r for r in PARAM_LIST if r[0] == edit_name)
                            new_val = max(vmin, min(vmax, new_val))  # borne aux limites
                            set_param(edit_name, new_val)
                        except (ValueError, StopIteration):
                            pass  # valeur invalide, on ignore
                        editing = False
                        edit_name = ""
                        edit_buffer = ""
                    elif event.key == pygame.K_ESCAPE:
                        # annule l'edition sans appliquer
                        editing = False
                        edit_name = ""
                        edit_buffer = ""
                    elif event.key == pygame.K_BACKSPACE:
                        edit_buffer = edit_buffer[:-1]  # efface le dernier caractere
                    elif event.unicode and (event.unicode.isdigit() or event.unicode in ".-eE"):
                        edit_buffer += event.unicode  # ajoute le caractere tape
                else:
                    # navigation dans la liste des parametres
                    if event.key == pygame.K_h:
                        config_help = not config_help  # affiche ou cache l'aide
                    elif event.key == pygame.K_UP:
                        param_index = (param_index - 1) % len(PARAM_LIST)  # remonte dans la liste
                    elif event.key == pygame.K_DOWN:
                        param_index = (param_index + 1) % len(PARAM_LIST)  # descend dans la liste
                    elif event.key == pygame.K_RIGHT:
                        SIM_SPEED = min(3.0, SIM_SPEED + 0.1)  # augmente la vitesse
                    elif event.key == pygame.K_LEFT:
                        SIM_SPEED = max(0.1, SIM_SPEED - 0.1)  # diminue la vitesse
                    elif event.key in (pygame.K_e, pygame.K_t):
                        # commence a editer le parametre selectionne
                        edit_name, _, _, _ = PARAM_LIST[param_index]
                        editing = True
                        edit_buffer = str(get_param(edit_name))
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                        name, step, _, _ = PARAM_LIST[param_index]
                        adjust_param(name, step)   # augmente d'un pas
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        name, step, _, _ = PARAM_LIST[param_index]
                        adjust_param(name, -step)  # diminue d'un pas
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        reset_simulation_state()
                        screen_state = "simulation"  # lance la simulation

        elif screen_state == "simulation":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if end_btn_rect.collidepoint(event.pos):
                    graph_surface = build_graph_surface()  # genere les graphiques
                    screen_state = "graph"  # passe a la page graphique

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    SIM_SPEED = min(5.0, round(SIM_SPEED + 0.2, 2))  # accelere
                elif event.key == pygame.K_LEFT:
                    SIM_SPEED = max(0.05, round(SIM_SPEED - 0.2, 2))  # ralentit
                elif event.key == pygame.K_f:
                    FAST_FORWARD = not FAST_FORWARD  # active ou desactive le turbo
                    print(f"Fast-Forward: {'ON' if FAST_FORWARD else 'OFF'} | Skip = {FAST_FORWARD_SKIP}")
                elif event.key == pygame.K_UP and FAST_FORWARD:
                    FAST_FORWARD_SKIP = min(500, FAST_FORWARD_SKIP + 10)  # plus de ticks par frame
                    print(f"Skip per frame: {FAST_FORWARD_SKIP}")
                elif event.key == pygame.K_DOWN and FAST_FORWARD:
                    FAST_FORWARD_SKIP = max(1, FAST_FORWARD_SKIP - 10)  # moins de ticks par frame
                    print(f"Skip per frame: {FAST_FORWARD_SKIP}")
                elif event.key == pygame.K_h:
                    show_ui = not show_ui  # affiche ou cache l'overlay des parametres

        elif screen_state == "graph":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if graph_reset_btn.collidepoint(event.pos):
                    # retour aux parametres depuis la page graphique
                    screen_state = "config"
                    editing = False
                    edit_name = ""
                    edit_buffer = ""

    # affichage selon l'etat courant de l'ecran

    if screen_state == "title":
        draw_title_page(screen)
        pygame.display.flip()  # met a jour l'affichage
        clock.tick(30)         # limite a 30 fps sur la page titre
        continue

    if screen_state == "config":
        draw_config_ui(screen, font)
        pygame.display.flip()
        clock.tick(30)
        continue

    if screen_state == "graph":
        graph_reset_btn = draw_graph_page(screen, graph_surface)
        pygame.display.flip()
        clock.tick(30)
        continue

    # Simulation
    ticks_this_frame = FAST_FORWARD_SKIP if FAST_FORWARD else 1  # un ou plusieurs ticks selon le mode

    for _ in range(ticks_this_frame):
        for o in prey:
            o.move()       # deplace chaque proie
        for o in predators:
            o.move()       # deplace chaque predateur

        all_orgs = prey + predators
        resolve_collisions(all_orgs, CELL_SIZE)  # gere les rebonds entre agents

        prey = resolve_predation(predators, prey)  # les predateurs mangent des proies

        for res in resources:
            res.spawn()                   # fait apparaitre de nouvelles ressources
        resolve_resources(prey, resources)  # les proies mangent les ressources

        for o in prey + predators:
            o.energy_cost()          # chaque agent perd de l'energie
            if o.eat_cooldown > 0:
                o.eat_cooldown -= 1  # reduit le delai apres avoir mange

        prey = [o for o in prey if o.energy > 0]           # retire les proies mortes
        predators = [o for o in predators if o.energy > 0] # retire les predateurs morts

        prey, predators = maybe_reinforce(prey, predators)  # reinsertion si extinction proche

        # reproduction de ceux qui ont assez d'energie
        new_prey = [o.reproduce() for o in prey if o.can_reproduce(len(prey))]
        new_preds = [o.reproduce() for o in predators if o.can_reproduce(len(predators))]
        prey.extend(new_prey)           # ajoute les nouveaux-nes a la liste
        predators.extend(new_preds)

        # sauvegarde les populations a ce tick pour le graphique final
        history_prey.append(len(prey))
        history_pred.append(len(predators))
        history_time.append(t)
        t += 1  # avance le compteur de temps

    # affichage graphique (saute des frames en mode turbo pour rester rapide)
    if not FAST_FORWARD or (frame_counter % max(1, FAST_FORWARD_SKIP // 8) == 0):
        screen.blit(background_surface, (0, 0))  # dessine le fond foret

        for r in resources:
            if r.amount > 0:
                draw_food(screen, r.x, r.y, r.kind, emoji_font)  # dessine la nourriture visible

        for o in prey:
            pygame.draw.circle(screen, (230, 0, 0), (int(o.x), int(o.y)), RADIUS)  # proie = cercle rouge

        for o in predators:
            direction = math.atan2(o.vy, o.vx)  # angle de deplacement du predateur
            mouth_open = 0.0 if o.eat_cooldown > 0 else (math.sin(t * 0.25) + 1) / 2  # bouche fermee apres avoir mange
            draw_pacman(screen, o.x, o.y, RADIUS, direction, mouth_open)  # dessine le predateur

        # compteurs de population en haut a gauche
        screen.blit(font.render(f"Proies: {len(prey)}", True, (230, 0, 0)), (10, 10))
        screen.blit(font.render(f"Predateurs: {len(predators)}", True, PACMAN_YELLOW), (10, 40))
        screen.blit(font.render("H: parametres | F: Turbo FF", True, (160, 160, 160)), (10, 68))  # rappel des touches

        # mini graphique en bas a droite
        graph_rect = pygame.Rect(WIDTH - 260, HEIGHT - 170, 240, 150)
        draw_mini_graph(screen, graph_rect, history_prey, history_pred)
        draw_legend(screen, WIDTH - 240, 10, font, blur_alpha=140)        # legende
        draw_speed_ui(screen, WIDTH - 240, 130, font, bold_font)          # vitesse
        draw_param_ui(screen, font)                                        # parametres (si visible)
        end_btn_rect = draw_end_button(screen, font)                       # bouton terminer
        pygame.display.flip()  # met a jour tout l'ecran

    # Vitesse ecran selon mode choisi
    if FAST_FORWARD:
        clock.tick(MAX_FPS_IN_FAST_MODE)           # fps eleve en turbo
    else:
        clock.tick(max(1, int(60 * SIM_SPEED)))    # fps ajuste selon la vitesse de simulation

pygame.quit()  # ferme pygame proprement a la fin
