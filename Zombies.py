import pygame, sys, math, random

#Setting up pygame and window
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SHUBHA game")
pygame.display.set_icon(pygame.image.load(r"Art\Player\Player_Pistol.png"))

class Timer:
    def __init__(self, time_to_finish):
        self.time_to_finish = time_to_finish

    def update(self):
        self.time_to_finish -= 1 / 60 # 60 = fps, 1/60 = delta time, accurate timer
        if self.time_to_finish <= 0:
            return True # returns true when finished

class UI:
    def draw(self, ui_type, text, font_size, color, rect, radius, pos): # values for text/rect
        if ui_type == "text":
            font = pygame.font.Font(r"Extras\Fonts\monogram.ttf", font_size) # makes font, renders text, blits to screen
            final_text = font.render(text, False, color) 
            window.blit(final_text, pos)
        elif ui_type == "rect": 
            pygame.draw.rect(window, color, rect, int(rect[3]/2), radius) # draws rect
            


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.delta_movement = [0, 0] # left/right, up/down
        self.speed = 4.5

        self.angle = 0

        self.bullets = [] # list of bullets
        self.can_shoot = True
        self.shooting_cooldown = 0.5 # timer for shooting
        self.shooting_timer = Timer(self.shooting_cooldown)

        self.hit_sfx = pygame.mixer.Sound(r"Extras\SFX\player_hit.wav") # load sfx
        self.shoot_sfx = pygame.mixer.Sound(r"Extras\SFX\shoot.wav")

        self.shoot_sfx.set_volume(0.07)

        self.hit_timer = Timer(0.2) # when zombie hits player, player briefly turns white for 0.2 secs
        self.hit = False

        self.fire_timer = Timer(5) # when fire zombie hits player, player is on fire for 5 secs
        self.ice_timer = Timer(3) # when ice zombie hits player, player is slowed for 3 secs

        self.fire_active = False # keeps track of if player is on fire/iced
        self.ice_active = False

        self.arsenal = ["Pistol"] # keeps track of all weapons player has bought/owns

        self.current_weapon_index = 0 # keeps track of current weapon from the arsenal list
        self.current_weapon = self.arsenal[self.current_weapon_index]

        self.bullet_damage = 20
        self.bullet_speed = 10

        self.reload_time_upgrade = 0 # upgrades for bullet speed, damage, and fire rate that you can buy in the shop
        self.bullet_damage_upgrade = 0
        self.bullet_speed_upgrade = 0

        self.max_health = 300
        self.health = 300

        self.dead = False


    def update(self):
        if not self.dead:
            self.get_input() # gets all input which controls movement and shooting
            self.move() # moves player
            self.aim() # finds angle of player from mouse pos
            self.update_gun_stats() # updates gun stats based on player's current weapon
            self.decrease_shoot_timer() # allows player to shoot when the timer is finished
            self.decrease_hit_timer() # makes player normal after timer finishes
            self.update_zombie_effects() # updates timers for if player got hit by fire/ice zombie
            self.contain_player() # stops player from going outside the screen

            self.current_weapon = self.arsenal[self.current_weapon_index] # updates current weapon based on index

            self.draw() # draws player

    def get_input(self):
        keystate = pygame.key.get_pressed() # gets all keys pressed

        if keystate[pygame.K_a] or keystate[pygame.K_LEFT]:
            self.delta_movement[0] = -1
        elif keystate[pygame.K_d] or keystate[pygame.K_RIGHT]:
            self.delta_movement[0] = 1
        else:
            self.delta_movement[0] = 0

        if keystate[pygame.K_w] or keystate[pygame.K_UP]:
            self.delta_movement[1] = -1
        elif keystate[pygame.K_s] or keystate[pygame.K_DOWN]:
            self.delta_movement[1] = 1
        else:
            self.delta_movement[1] = 0

        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot() # shoots when mouse pressed down

    def move(self):
        self.x += self.delta_movement[0] * self.speed # moves player based on delta movement
        self.y += self.delta_movement[1] * self.speed

    def draw(self):
        if self.fire_active: # if fire active, player is red and diff image is loaded
            image = pygame.image.load(rf"Art\Player\Player_{self.current_weapon}_Fire.png").convert_alpha()
        elif self.ice_active: # if ice active, player is blue and diff image is loaded
            image = pygame.image.load(rf"Art\Player\Player_{self.current_weapon}_Iced.png").convert_alpha()
        else:
            image = pygame.image.load(rf"Art\Player\Player_{self.current_weapon}.png").convert_alpha()

        new_img, new_rect = self.rotate(image)

        if self.hit: # if hit, it makes a white image instead of normal
            final_img = self.create_white_surf(new_img, 128)
            window.blit(final_img, new_rect)
        else:
            window.blit(new_img, new_rect)

    def aim(self):
        mouse_x, mouse_y = pygame.mouse.get_pos() # gets distance between mouse and player
        dx = self.x - mouse_x
        dy = self.y - mouse_y

        self.angle = math.degrees(math.atan2(dy, -dx)) # uses trig to find angle

    def shoot(self):
        gun_pos_x = math.cos(math.radians(self.angle)) * 20 # gets pos of gun to add to the bullet
        gun_pos_y = -math.sin(math.radians(self.angle)) * 20

        if self.current_weapon == "Sniper": # if sniper, bullet is invincible and will go right through zombies
            bullet = Bullet(self.x + gun_pos_x, self.y + gun_pos_y, self.angle, self.bullet_damage, self.bullet_speed, True)
        else:
            bullet = Bullet(self.x + gun_pos_x, self.y + gun_pos_y, self.angle, self.bullet_damage, self.bullet_speed, False) # makes bullet and adds gun pos to make it look like the bullet comes out of the gun
        
        if self.current_weapon == "Shotgun": # if shotgun active, shoots 3 bullets
            left_bullet = Bullet(self.x + gun_pos_x, self.y + gun_pos_y - 10, self.angle + 15, self.bullet_damage, self.bullet_speed, False)
            right_bullet = Bullet(self.x + gun_pos_x, self.y + gun_pos_y + 10, self.angle - 15, self.bullet_damage, self.bullet_speed, False)

            self.bullets.append(left_bullet)
            self.bullets.append(right_bullet)
        
        self.bullets.append(bullet)
        self.shoot_sfx.play()

        self.can_shoot = False

    def decrease_shoot_timer(self):
        if not self.can_shoot and self.shooting_timer.update(): # when timer finished, the player can shoot again and new timer made
            self.can_shoot = True
            self.shooting_timer = Timer(self.shooting_cooldown)

    def decrease_hit_timer(self):
        if self.hit:
            if self.hit_timer.update(): # when hit timer finishes, player turns normal again and new timer made
                self.hit = False
                self.hit_timer = Timer(0.2)


    def update_bullets(self, zombies):
        for bullet in self.bullets: # updates all bullets and checks if bullet has collided with zombie
            bullet.update()
            for zombie in zombies:
                bullet.collide(zombie)

    def update_gun_stats(self): # updates gun stats based on current weapon and upgrades
        if self.current_weapon == "Pistol":
            self.shooting_cooldown = 0.5 - self.reload_time_upgrade
            self.bullet_damage = 20 + self.bullet_damage_upgrade
            self.bullet_speed = 10 + self.bullet_speed_upgrade
        elif self.current_weapon == "Shotgun":
            self.shooting_cooldown = 0.75 - self.reload_time_upgrade
            self.bullet_damage = 30 + self.bullet_damage_upgrade
            self.bullet_speed = 10 + self.bullet_speed_upgrade
        elif self.current_weapon == "Sniper":
            self.shooting_cooldown = 1.5 - self.reload_time_upgrade
            self.bullet_damage = 50 + self.bullet_damage_upgrade
            self.bullet_speed = 15 + self.bullet_speed_upgrade
        elif self.current_weapon == "Machine_Gun":
            self.shooting_cooldown = 0.1 - self.reload_time_upgrade
            self.bullet_damage = 15 + self.bullet_damage_upgrade
            self.bullet_speed = 10 + self.bullet_speed_upgrade
        

    def rotate(self, image):
        rotated_image = pygame.transform.rotate(image, self.angle) # rotate image
        new_rect = image.get_rect(center=(self.x, self.y))
        new_rect = rotated_image.get_rect(center = new_rect.center) # gets new pos
        return rotated_image, new_rect

    def inflict_damage(self, damage, zombie_type):
        self.health -= damage
        self.hit = True # turns player white

        self.check_zombie_effects(zombie_type) # ices or sets on fire based on zombie type

        if self.health <= 0:
            self.dead = True

        self.hit_sfx.play() # plays hit sfx

    def heal(self, amount):
        self.health += amount
        if self.health > self.max_health: # makes sure health doesnt go over max health
            self.health = self.max_health

    def check_zombie_effects(self, zombie_type):
        if zombie_type == "Ice":
            self.ice_active = True
        elif zombie_type == "Fire":
            self.fire_active = True

    def update_zombie_effects(self):
        if self.ice_active:
            if self.ice_timer.update(): # updates and checks if ice timer is finished, otherwise slows player
                self.ice_active = False
                self.ice_timer = Timer(3)
            else:
                self.speed = 1.5
        else:
            self.speed = 4.5 # if not iced, speed is normal
        if self.fire_active:
            if self.fire_timer.update(): # updates and checks if fire timer is finished, otherwise damages player continuously over time
                self.fire_active = False
                self.fire_timer = Timer(5)
            else:
                self.health -= 0.17 # loses 0.17 health per frame, 10 per second

    def create_white_surf(self, surf, alpha): # copied from stack overflow ;)
        mask = pygame.mask.from_surface(surf)
        white_surface = mask.to_surface()
        white_surface.set_colorkey((0, 0, 0))
        white_surface.set_alpha(alpha)
        return white_surface

    def contain_player(self): # stops player from exiting screen
        if self.x > 1260:
            self.x = 1260
        if self.x < 20:
            self.x = 20
        if self.y > 700:
            self.y = 700
        if self.y < 20:
             self.y = 20   

class Bullet:
    def __init__(self, x, y, angle, damage, speed, invincible):
        self.x = x
        self.y = y
        self.angle = angle

        self.speed = speed

        self.dx = 0
        self.dy = 0

        self.collision_tollerance = 88 # width of the biggest zombie
        self.damage = damage

        self.dead = False
        self.invincible = invincible # if invincible, bullet doesnt die when it hits a zombie
        self.hit_zombies = [] # keeps track of zombies hit by bullet to prevent bullet from damaging same zombie multiple times

        self.calc_init_movement()
        self.calc_init_image()

    def calc_init_movement(self): # calculates initial movement here because the bullet travels in a straight line
        self.dx = math.cos(math.radians(self.angle))
        self.dy = math.sin(math.radians(self.angle))

    def calc_init_image(self): # calculates init image because it will always be the same
        self.image = pygame.image.load(r"Art\Bullet\bullet.png").convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (15, 6))

    def update(self):
        if not self.dead:
            self.move() # uses dx, dy to move
            self.draw() # draws bullet
            self.contain_bullet()

    def move(self):
        self.x += self.dx * self.speed # moves bullet bbased on dx, dy and speed
        self.y -= self.dy * self.speed

    def draw(self):
        new_img, new_rect = self.rotate(self.image)
        window.blit(new_img, new_rect)

    def rotate(self, image): # same as player function
        rotated_image = pygame.transform.rotate(image, self.angle) # rotate image
        new_rect = image.get_rect(center=(self.x, self.y))
        new_rect = rotated_image.get_rect(center = new_rect.center)
        return rotated_image, new_rect

    def collide(self, zombie): # checks for collision
        dx, dy = zombie.x - self.x, zombie.y - self.y
        distance = math.hypot(dx, dy) # gets distance between zombie and bullet with pythag theorm

        if distance < self.collision_tollerance: # checks if bullet is even remotely close to zombie
            collision_tollerance = zombie.image.get_height() # sets tollerance to zombie height because that's the side that faces the player
            if distance <  collision_tollerance and not self.dead and not zombie.dead: # check if the bullet is super close / coliding
                if zombie not in self.hit_zombies: # checks if zombie has already been hit by bullet
                    zombie.inflict_damage(self.damage) # damages zombie
                    self.hit_zombies.append(zombie) # adds zombie to hit zombies list
                    if not self.invincible: # if not invincible, bullet dies
                        self.dead = True

    def contain_bullet(self):
        if self.x > 1280 or self.x < 0 or self.y > 720 or self.y < 0:
            self.dead = True # if bullet goes off screen, it dies

class Particle: # blood effect for zombie
    def __init__(self, x, y, x_vel, y_vel, size, decrement, speed, color): 
        self.x = x
        self.y = y

        self.x_velocity = x_vel
        self.y_velocity = y_vel

        self.size = size
        self.decrement = decrement # controls how fast the particle shrinks and disappears

        self.color = color

        self.speed = speed

    def update(self):
        self.x += self.x_velocity * self.speed # uses vel and speed to move particle
        self.y += self.y_velocity * self.speed

        self.size -= self.decrement # since particle = rect, making the size smaller over time will make the particle smaller and then eventully disappear
    
        pygame.draw.rect(window, self.color, (self.x, self.y, self.size, self.size)) # draws particle

class Medkit:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.image = pygame.image.load(r"Art\Medkit\medkit.png").convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (32, 32))

        self.pickup_sfx = pygame.mixer.Sound(r"Extras\SFX\powerup.wav")
        self.pickup_sfx.set_volume(0.65)

        self.collision_tollerance = 40

        self.dead = False

    def update(self, player):
        if not self.dead:
            self.draw()
            self.collide(player)

    def draw(self):
        window.blit(self.image, (self.x, self.y))

    def collide(self, player): # checks for collision with player
        dx = player.x - self.x
        dy = player.y - self.y

        distance = math.hypot(dx, dy)

        if distance < self.collision_tollerance:
            player.heal(30)
            self.pickup_sfx.play()
            self.dead = True

class Zombie:
    def __init__(self, x, y, speed, damage, health, zombie_type, reward, particle_intensity):
        self.x = x
        self.y = y

        self.speed = speed
        self.damage = damage
        self.type = zombie_type

        self.angle = 0

        self.collision_tollerance = 50

        self.hit = False
        self.hit_timer = Timer(0.1) # same hit timer as player but quicker

        self.dead_next_time = False # when a zombie is hit, i want it to flash white, and THEN die. this var allows me to keep track of whether it needs to die

        self.reward = reward # score increment for when it dies
        
        self.damaged_player = False

        self.dead = False
        self.health = health

        self.hit_sfx = pygame.mixer.Sound(r"Extras\SFX\zombie_hit.wav")
        self.dead_sfx = pygame.mixer.Sound(r"Extras\SFX\zombie_dead.wav")

        self.hit_sfx.set_volume(0.3)
        self.dead_sfx.set_volume(0.35)

        self.particles = [] # list of all particles made by the zombie
        self.particle_intensity = particle_intensity # controls how many particles spawn

        self.calc_init_image()

    def update(self, player_x, player_y):
        if not self.dead:
            dx, dy = self.look_at_player(player_x, player_y) # makes the zombie loook towards the player
            self.move(dx, dy) # moves towards player
            self.draw() # draws zombie
            self.decrease_hit_timer() # hit timer for when it flashes white

    def calc_init_image(self):
        self.image = pygame.image.load(rf"Art\Zombies\{self.type}.png") # image stays the same, might as well do it here

    def look_at_player(self, player_x, player_y): # player aim and bullet move functions merged together
        dx = self.x - player_x
        dy = self.y - player_y

        self.angle = math.degrees(math.atan2(dy, -dx))

        dx = math.cos(math.radians(self.angle))
        dy = math.sin(math.radians(self.angle))

        return dx, dy

    def move(self, dx, dy): # uses look at player to move 
        self.x += dx * self.speed
        self.y -= dy * self.speed

    def draw(self):
        new_img, new_rect = self.rotate(self.image)
        if self.hit:
            final_img = self.create_white_surf(new_img, 128) # makes it white when zombie hit
            window.blit(final_img, new_rect)
        else:
            window.blit(new_img, new_rect)

    def rotate(self, image):
        rotated_image = pygame.transform.rotate(image, self.angle + 90) # rotate image, 90 degrees because the image is facing right by default but it should be facing down
        new_rect = image.get_rect(center=(self.x, self.y))
        new_rect = rotated_image.get_rect(center = new_rect.center)
        return rotated_image, new_rect

    def inflict_damage(self, damage):
        self.health -= damage
        self.hit = True

        if self.health <= 0 and self.hit:
            self.dead_next_time = True
            self.dead_sfx.play()
        else:
            self.hit_sfx.play()


    def collide(self, player): # basically same as bullet func
        dx, dy = player.x - self.x, player.y - self.y
        distance = math.hypot(dx, dy)

        if distance < self.collision_tollerance and not self.dead and not player.dead:
            player.inflict_damage(self.damage, self.type) # damages player if it collides
            self.damaged_player = True
            self.dead = True
    
    def decrease_hit_timer(self):
        if self.hit:
            if self.hit_timer.update():
                self.hit = False
                self.hit_timer = Timer(0.15)

                if self.dead_next_time: # checks if the zombie was waiting to finish flashing white to die
                    self.dead = True
                    self.dead_next_time = False
            else:
                if self.dead_next_time: # if zombie is still flashing white but needs to die, zombie starts making particles because its bout to die
                    for i in range(self.particle_intensity): # particle intensity * (0.1 * 60) = num of particle
                        x_vel, y_vel =  random.randint(0, 20) / 10 - 1, random.randint(0, 20) / 10 - 1 # calc random x and y vels
                        particle = Particle(self.x, self.y, x_vel, y_vel, random.randint(7, 9), 0.35, 5, (172, 50, 50)) # creates new particle
                        self.particles.append(particle) # adds to list
            

    def update_particles(self):
        old_particles = self.particles # need this because you shouldn't remove an element from the list while a for loop is iterating through it
        for particle in self.particles:
            particle.update() # updates particles
             
            if particle.size <= 0:
                old_particles.remove(particle) # removes particle from OLD list (but really its the same)
        self.particles = old_particles # sets it back now, AFTER the for loop is done

    def create_white_surf(self, surf, alpha): # same as player func
        mask = pygame.mask.from_surface(surf)
        white_surface = mask.to_surface()
        white_surface.set_colorkey((0, 0, 0))
        white_surface.set_alpha(alpha)
        return white_surface


class ZombieSpawner:
    def __init__(self):
        self.zombie_cooldown = 1.5 # time between each zombie spawn
        self.zombie_timer = Timer(self.zombie_cooldown)

        self.zombie_health_addon = 0 # increases zombie health by this amount every time a new wave spawns

        self.zombies = [] # list of all zombies

    def update(self):
        self.decrease_timer()

    def decrease_timer(self):
        if self.zombie_timer.update(): # if timer is done, spawn zombie
            self.spawn_zombie()
            self.zombie_timer = Timer(self.zombie_cooldown)

    def spawn_zombie(self):
        x, y = self.calc_pos()
        speed, damage, health, zombie_type, reward, particle_intensity = self.determine_stats()

        zombie = Zombie(x, y, speed, damage, health, zombie_type, reward, particle_intensity)
        self.zombies.append(zombie)

    def calc_pos(self):
        general_direction = random.randint(1, 2) # 1 = left/right, 2 = up/down
        specific_direction = random.randint(1, 2) # 1 = left/up, 2 = right/down

        if general_direction == 1 and specific_direction == 1: # 4 quadrants, this is left
            x = -10
            y = random.randint(0, 720)
        if general_direction == 1 and specific_direction == 2: # right
            x = 1290
            y = random.randint(0, 720)
        if general_direction == 2 and specific_direction == 1: # up
            x = random.randint(0, 1280)
            y = -10
        if general_direction == 2 and specific_direction == 2: # down
            x = random.randint(0, 1280)
            y = 730

        return x, y # returns random position

    def determine_stats(self):
        rand_type = random.randint(1, 100) # generates random number between 1 and 100

        if rand_type < 50: # uses if and elif statements to pick a type
            zombie_type = "Small" # and sets the stats accordingly
            speed = 3
            damage = 10
            health = 17 + self.zombie_health_addon
            reward = 100
            particle_intensity = 3
        elif rand_type < 60:
            zombie_type = "Fast"
            speed = 5
            damage = 15
            health = 15 + self.zombie_health_addon
            reward = 200
            particle_intensity = 2
        elif rand_type < 65:
            zombie_type = "Ice"
            speed = 3.5
            damage = 25
            health = 37 + self.zombie_health_addon
            reward = 400
            particle_intensity = 3
        elif rand_type < 70:
            zombie_type = "Fire"
            speed = 3.5
            damage = 10
            health = 37 + self.zombie_health_addon
            reward = 400
            particle_intensity = 3
        elif rand_type < 93:
            zombie_type = "Medium"
            speed = 2.25
            damage = 20
            health = 47 + self.zombie_health_addon
            reward = 300
            particle_intensity = 4
        elif rand_type <= 100:
            zombie_type = "Big"
            speed = 1.5
            damage = 35
            health = 97 + self.zombie_health_addon
            reward = 500
            particle_intensity = 6

        return speed, damage, health, zombie_type, reward, particle_intensity # returns all stats

    def update_zombies(self, player): # updates all zombies
        for zombie in self.zombies:
            if not zombie.dead:
                zombie.update(player.x, player.y) # updates zombie
                zombie.collide(player) # checks if zombie collides with player
            zombie.update_particles() # updates particles

class Button:
    def __init__(self, x, y, rect, rect_radius, button_text, font_size, rect_color, button_color, highlight_color):
        self.x = x
        self.y = y

        self.rect = rect
        self.rect_radius = rect_radius # for rounded corners on the rect

        self.button_text = button_text
        self.font_size = font_size

        self.normal_rect_color = rect_color # bg color
        self.current_color = self.normal_rect_color # currennt bg color
        self.highlight_color = highlight_color # bg color if hovered over
        self.button_color = button_color # text color

        self.ui = UI()

        self.hover_sfx = pygame.mixer.Sound(r"Extras\SFX\hover.wav") # loads sound effect and sets volume
        self.select_sfx = pygame.mixer.Sound(r"Extras\SFX\select.wav")

        self.hover_sfx.set_volume(0.3)
        self.select_sfx.set_volume(0.5)

        self.hovering = False # if mouse is hovering over button
        self.pressed = False # if mouse is pressed on button
        self.let_go = True # if mouse has let go of button

    def update(self):
        self.check_if_hovering()
        self.check_if_pressed()
        self.draw()

    def draw(self): # draws rect and text with the ui class
        self.ui.draw("rect", None, None, self.current_color, self.rect, self.rect_radius, None)

        self.ui.draw("text", self.button_text, self.font_size, self.button_color, None, None, (self.x, self.y))

    def check_if_hovering(self):
        mouse_x, mouse_y = pygame.mouse.get_pos() # gets mouse position
        was_hovering = self.hovering

        if mouse_x > self.rect[0] and mouse_x < self.rect[0] + self.rect[2] and mouse_y > self.rect[1] and mouse_y < self.rect[1] + self.rect[3]: # checks if pos is within rect
            self.hovering = True # sets hovering to true and changes color
            self.current_color = self.highlight_color
        else:
            self.hovering = False # reverses if not hovering
            self.current_color = self.normal_rect_color

        if self.hovering and not was_hovering: # only plays sound if it was not hovering before
            self.hover_sfx.play()

    def check_if_pressed(self):
        self.pressed = False
        if pygame.mouse.get_pressed()[0]:
            if self.hovering and self.let_go: # if mouse is pressed and hovering and has let go, prevents spamming
                self.pressed = True
                self.select_sfx.play() # plays sound
            self.let_go = False # sets let go to false if mouse is pressed

        if not self.let_go and not pygame.mouse.get_pressed()[0]: # sets let go to true if mouse is not pressed
            self.let_go = True

class Shop:
    def __init__(self, game):
        self.game = game
        self.ui = UI()

        self.shotgun_button = Button(270, 190, (220, 180, 260, 250), 4, "SHOTGUN", 60, (30, 30, 30), (172, 50, 50), (50, 50, 50)) # loads all buttons
        self.sniper_button = Button(580, 190, (520, 180, 260, 250), 4, "SNIPER", 60, (30, 30, 30), (172, 50, 50), (50, 50, 50))
        self.machine_gun_button = Button(845, 190, (820, 180, 260, 250), 4, "MACHINE GUN", 50, (30, 30, 30), (172, 50, 50), (50, 50, 50))

        self.reload_time_button = Button(250, 515, (220, 505, 260, 150), 4, "INCREASE FIRE RATE", 30, (30, 30, 30), (172, 50, 50), (50, 50, 50))
        self.bullet_damage_button = Button(530, 515, (520, 505, 260, 150), 4, "INCREASE BULLET DAMAGE", 30, (30, 30, 30), (172, 50, 50), (50, 50, 50))
        self.bullet_speed_button = Button(835, 515, (820, 505, 260, 150), 4, "INCREASE BULLET SPEED", 30, (30, 30, 30), (172, 50, 50), (50, 50, 50))

        self.reload_time_price = 300 # prices for upgrades since they change
        self.bullet_damage_price = 200
        self.bullet_speed_price = 50

        self.active = False # if shop is currently open

    def update(self):
        if self.active:
            self.draw_shop() # draws shop

            self.shotgun_button.update() # updates all buttons
            self.sniper_button.update()
            self.machine_gun_button.update()

            self.reload_time_button.update()
            self.bullet_damage_button.update()
            self.bullet_speed_button.update()

            self.get_gun_buttons_pressed() # checks if any buttons are pressed and completes the transaction
            self.get_gun_upgrades_pressed()

            self.draw_button_text() # prices
            self.draw_gun_images() # gun images

    def draw_shop(self): # draws grey rect, writes shop and upgrades
        self.ui.draw("rect", None, None, (100, 100, 100), (200, 100, 900, 580), 4, None)
        self.ui.draw("text", "SHOP", 50, (100, 25, 25), None, None, (615, 120))

        self.ui.draw("text", "UPGRADES", 50, (100, 25, 25), None, None, (570, 445))

    def draw_button_text(self): # draws all prices
        self.ui.draw("text", "$500", 50, (172, 50, 50), None, None, (300, 230))
        self.ui.draw("text", "$1000", 50, (172, 50, 50), None, None, (600, 230))
        self.ui.draw("text", "$2000", 50, (172, 50, 50), None, None, (890, 230))

        self.ui.draw("text", f"${self.reload_time_price}", 40, (172, 50, 50), None, None, (320, 540))
        self.ui.draw("text", f"${self.bullet_damage_price}", 40, (172, 50, 50), None, None, (610, 540))
        self.ui.draw("text", f"${self.bullet_speed_price}", 40, (172, 50, 50), None, None, (910, 540))

    def draw_gun_images(self): # draws all gun images
        shotgun_img = pygame.transform.scale(pygame.image.load(r"Art\Shop\Shotgun.png"), (165, 60))
        sniper_img = pygame.transform.scale(pygame.image.load(r"Art\Shop\Sniper.png"), (201, 45))
        machine_gun_img = pygame.transform.scale(pygame.image.load(r"Art\Shop\MachineGun.png"), (225, 90))

        window.blit(shotgun_img, (260, 340))
        window.blit(sniper_img, (550, 340))
        window.blit(machine_gun_img, (840, 330))

    def get_gun_buttons_pressed(self):
        if self.shotgun_button.pressed and not "Shotgun" in self.game.player.arsenal: # checks if button is pressed and that the player doesn't already have the gun
            if self.complete_transaction(500): # if player has enough money, deduct it and add the gun to arsenal
                self.game.player.arsenal.append("Shotgun")

        if self.sniper_button.pressed and not "Sniper" in self.game.player.arsenal:
            if self.complete_transaction(1000):
                self.game.player.arsenal.append("Sniper")

        if self.machine_gun_button.pressed and not "Machine_Gun" in self.game.player.arsenal:
            if self.complete_transaction(2000):
                self.game.player.arsenal.append("Machine_Gun")

    def get_gun_upgrades_pressed(self):
        if self.reload_time_button.pressed: # check if pressed
            if self.complete_transaction(self.reload_time_price): # check if player has enough money and buy it
                self.game.player.reload_time_upgrade += 0.05 # upgrade reload time and increase price
                self.reload_time_price += int(75 * (self.reload_time_price / 100))

        if self.bullet_damage_button.pressed:
            if self.complete_transaction(self.bullet_damage_price):
                self.game.player.bullet_damage_upgrade += 5
                self.bullet_damage_price += int(50 * (self.bullet_damage_price / 100))

        if self.bullet_speed_button.pressed:
            if self.complete_transaction(self.bullet_speed_price):
                self.game.player.bullet_speed_upgrade += 1
                self.bullet_speed_price += int(40 * (self.bullet_speed_price / 100))
        

    def complete_transaction(self, item_cost):
        if self.game.money >= item_cost: # check if player has enough money
            self.game.money -= item_cost # deduct money
            return True # return true if transaction is complete
        return False

class MainMenu:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.ui = UI()

        self.active = True # if main menu is currently open

        pygame.mixer.music.set_volume(0.6) # load music
        pygame.mixer.music.load(r"Extras\Music\DarkZombieSC.wav")
        pygame.mixer.music.play(-1) # -1 means it loops infinitely

        self.play_button = Button(550, 300, (540, 315, 150, 50), 0, "PLAY", 90, (170, 170, 170), (172, 50, 50), (200, 200, 200)) # load buttons
        self.quit_button = Button(550, 400, (540, 415, 150, 50), 0, "QUIT", 90, (170, 170, 170), (172, 50, 50), (200, 200, 200))

        self.update()

    def update(self):
        while self.running: # new while loop for main menu
            window.fill((170, 170, 170))
            self.check_if_quit() # checks if X button is pressed

            self.draw() # draws the buttons and text
            self.check_if_pressed() # checks if buttons are pressed

            pygame.display.update()
            self.clock.tick(self.fps)

    def check_if_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def draw(self):
        self.ui.draw("text", "ZOMBIE SHOOTOUT", 150, (172, 50, 50), None, None, (220, 150))
        self.play_button.update() # updates buttons
        self.quit_button.update()

    def check_if_pressed(self):
        if self.play_button.pressed: # if play button is pressed, call Game class and pause music so it can resume in game, prevents music from restarting
            pygame.mixer.music.pause()
            Game()

        if self.quit_button.pressed: # quit
            pygame.quit()
            sys.exit()

class Game:
    def __init__(self):
        self.running = True
        self.fps = 60
        self.clock = pygame.time.Clock()

        self.player = Player(300, 300) # player and zombie spawner
        self.zombie_spawner = ZombieSpawner()

        self.score = 0 # stats for game
        self.money = 0

        self.wave_cooldown = 30 # cooldown for next wave
        self.wave_timer = Timer(self.wave_cooldown)
        self.wave = 0 # current wave

        self.medkit_cooldown = 45 # cooldown for medkit
        self.medkit_timer = Timer(self.medkit_cooldown)
        self.medkits = [] # list of medkits

        pygame.mixer.music.unpause() # unpause music from main menu since it was paused there, music handoff complete

        self.game_over = False

        self.ui = UI()
        self.shop = Shop(self) # pass in self so shop can access game class variables

        self.run()


    def run(self):
        while self.running:
            window.fill((170, 170, 170)) # fill window with grey and check if quit no matter what
            self.check_input() # check for input

            if not self.shop.active: # if shop isn't active, run game
                self.player.update() # update player and bullets
                self.player.update_bullets(self.zombie_spawner.zombies) # pass in zombies so that bullets can check if they hit a zombie

                self.zombie_spawner.update() # updates zombies
                self.zombie_spawner.update_zombies(self.player) # pass in player so that zombies can check if they hit the player

                self.remove_entity(self.player.bullets, self.zombie_spawner.zombies) # remove bullets and zombies from the game if they are dead

                self.draw_health_bar() # draw health bar and stats
                self.draw_stats()

                self.advance_wave() # advance wave if cooldown is over and also draw it 
                self.draw_wave()

                self.spawn_medkits() # spawn and update medkits
                self.update_medkits()

                self.shop.update() # update the shop

                self.end_game() # draw game over screen if player is dead
            else:
                self.display_shop_and_stats() # otehrwise display shop and stats

            pygame.display.update() # also update display no matter what
            self.clock.tick(self.fps)

    def check_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # check if quit
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and self.game_over: # restart game if space is pressed and game is over
                    self.game_over = False
                    self.__init__() # restart game
                if event.key == pygame.K_p: # open shop if p pressed
                    if self.shop.active:
                        self.shop.active = False
                    else:
                        self.shop.active = True 
                if event.key == pygame.K_TAB: # if tab pressed, switch weapon
                    weapon_index = self.player.current_weapon_index
                    weapon_index += 1
                    if weapon_index > len(self.player.arsenal) - 1: # if weapon index goes out of range, set it to 0
                        weapon_index = 0
                    self.player.current_weapon_index = weapon_index

    def remove_entity(self, bullets, zombies):
        for bullet in bullets: # removes bullets and zombies if they are dead
            if bullet.dead:
                bullets.remove(bullet)

        for zombie in zombies:
            if zombie.dead and not zombie.damaged_player and zombie.particles == []: # if zombie partcles gone, remove zombie
                zombies.remove(zombie)
                self.score += zombie.reward # reward player for killing zombie
                self.money += (zombie.reward / 15)

    def draw_health_bar(self):
        self.ui.draw("rect", None, None, (255, 0, 70), (20, 25, 300, 26), 2, None) # draws red bar first
        if self.player.health >= 0:
            self.ui.draw("rect", None, None, (55, 148, 110), (20, 25, self.player.health, 26), 2, None) # then draws green bar on top to show health

    def draw_stats(self): # draws stats
        self.ui.draw("text", f"SCORE: {self.score}", 40, (172, 50, 50), None, None, (20, 65))
        self.ui.draw("text", f"${int(self.money)}", 40, (172, 50, 50), None, None, (20, 100))
        self.ui.draw("text", f"Current Weapon: {self.player.current_weapon}", 30, (172, 50, 50), None, None, (1100 - (len(self.player.current_weapon)) * 12, 30))

    def draw_wave(self): # draws wave
        self.ui.draw("text", f"WAVE {self.wave}", 50, (172, 50, 50), None, None, (600, 20))

    def advance_wave(self):
        if self.wave_timer.update(): # if cooldown is over, advance wave
            self.wave += 1
            self.wave_timer = Timer(self.wave_cooldown)

            if self.zombie_spawner.zombie_cooldown >= 0.2: # if cooldown is greater than 0.2, decrease it by 0.1, stops game from becoming impossible
                self.zombie_spawner.zombie_cooldown -= 0.1
            else: # otherwise, just add a lot of health every wave so it still gets harder
                self.zombie_spawner.zombie_health_addon += 3
                
            self.zombie_spawner.zombie_health_addon += 1

            self.medkit_cooldown -= 1 # medkit cooldown decreases by 1 every wave

    def display_shop_and_stats(self):
        self.shop.update() # if shop open, update shop and display stats

        self.draw_health_bar()
        self.draw_stats()
        self.draw_wave()

    def spawn_medkits(self):
        if self.medkit_timer.update(): # if cooldown is over, spawn medkit
            self.medkit_timer = Timer(self.medkit_cooldown)

            rand_x, rand_y = random.randint(80, 1200), random.randint(120, 600) # calc random x and y
            medkit = Medkit(rand_x, rand_y) # make new medkit
            self.medkits.append(medkit) # add to list

    def update_medkits(self):
        for medkit in self.medkits: # iterate through medkits and update all of them
            medkit.update(self.player)
            if medkit.dead: # if medkit is dead, remove it
                self.medkits.remove(medkit)
            

    def end_game(self):
        if self.player.dead: # if player is dead, draw game over screen
            window.fill((170, 170, 170))
            self.ui.draw("text", "GAME OVER", 110, (172, 50, 50), None, None, (440, 200))
            self.ui.draw("text", f"Score: {self.score}", 60, (172, 50, 50), None, None, (540 - (len(str(self.score)) * 10), 300))
            self.ui.draw("text", "[Space] to Restart", 42, (172, 50, 50), None, None, (485, 380))
            self.game_over = True
        

MainMenu() # game starts from the main menu screen