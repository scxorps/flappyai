import pygame  # Import the pygame module for game development
import neat  # Import the NEAT module for neuroevolution
import time  # Import the time module
import random  # Import the random module for generating random numbers
import os  # Import the os module for file path operations
import pickle  # Import the pickle module for saving and loading data
pygame.font.init()  # Initialize the pygame font module

WIN_WIDTH = 500  # Set the width of the game window
WIN_HEIGHT = 800  # Set the height of the game window

BIRD_IMGS = [  # Load and scale bird images
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), 
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), 
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))  # Load and scale pipe image
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))  # Load and scale base image
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))  # Load and scale background image

STAT_FONT = pygame.font.SysFont("comicsans", 50)  # Set the font for displaying text
gen = -1  # Initialize generation count
high_score = 0  # Initialize highest score
class Bird:
    IMGS = BIRD_IMGS  # Set bird images
    MAX_ROTATION = 25  # Set maximum rotation angle
    ROT_VEL = 20  # Set rotation velocity
    ANIMATION_TIME = 5  # Set animation time

    def __init__(self, x, y):
        self.x = x  # Set initial x-coordinate
        self.y = y  # Set initial y-coordinate
        self.tilt = 0  # Set initial tilt angle
        self.tick_count = 0  # Initialize tick count
        self.vel = 0  # Set initial velocity
        self.height = self.y  # Set initial height
        self.img_count = 0  # Initialize image count
        self.img = self.IMGS[0]  # Set initial image

    def jump(self):
        self.vel = -10.5  # Set jump velocity
        self.tick_count = 0  # Reset tick count
        self.height = self.y  # Set height to current y-coordinate

    def move(self):
        self.tick_count += 1  # Increment tick count
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2  # Calculate displacement
        if d >= 16:
            d = 16  # Limit displacement to 16
        if d < 0:
            d -= 2  # Make bird jump higher
        self.y = self.y + d  # Update y-coordinate
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION  # Tilt bird upwards
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL  # Tilt bird downwards

    def draw(self, win):
        self.img_count += 1  # Increment image count
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]  # Display first image
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]  # Display second image
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]  # Display third image
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]  # Display second image
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]  # Reset image count and display first image
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMGS[1]  # Display second image when tilted downwards
            self.img_count = self.ANIMATION_TIME * 2
        rotated_image = pygame.transform.rotate(self.img, self.tilt)  # Rotate bird image
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)  # Get rectangle of rotated image
        win.blit(rotated_image, new_rect.topleft)  # Display rotated image

    def get_mask(self):
        return pygame.mask.from_surface(self.img)  # Return mask of bird image

class Pipe:
    GAP = 170  # Set gap between pipes
    VEL = 10  # Set pipe velocity

    def __init__(self, x):
        self.x = x  # Set initial x-coordinate
        self.height = 0  # Initialize height
        self.GAP = 170  # Set gap between pipes
        self.top = 0  # Initialize top pipe position
        self.bottom = 0  # Initialize bottom pipe position
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)  # Load and flip top pipe image
        self.PIPE_BOTTOM = PIPE_IMG  # Load bottom pipe image
        self.passed = False  # Initialize passed flag
        self.set_height()  # Set pipe height

    def set_height(self):
        self.height = random.randrange(50, 450)  # Set random height for pipes
        self.top = self.height - self.PIPE_TOP.get_height()  # Calculate top pipe position
        self.bottom = self.height + self.GAP  # Calculate bottom pipe position

    def move(self):
        self.x -= self.VEL  # Move pipe leftwards

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))  # Display top pipe
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))  # Display bottom pipe

    def collide(self, bird):
        bird_mask = bird.get_mask()  # Get bird mask
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)  # Get top pipe mask
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)  # Get bottom pipe mask
        top_offset = (self.x - bird.x, self.top - round(bird.y))  # Calculate top pipe offset
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))  # Calculate bottom pipe offset
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)  # Check for collision with bottom pipe
        t_point = bird_mask.overlap(top_mask, top_offset)  # Check for collision with top pipe
        if b_point or t_point:
            return True  # Collision detected
        return False  # No collision

class Base:
    VEL = 10  # Set base velocity
    WIDTH = BASE_IMG.get_width()  # Get base image width
    IMG = BASE_IMG  # Set base image

    def __init__(self, y):
        self.y = y  # Set initial y-coordinate
        self.x1 = 0  # Initialize first base image x-coordinate
        self.x2 = self.WIDTH  # Initialize second base image x-coordinate

    def move(self):
        self.x1 -= self.VEL  # Move first base image leftwards
        self.x2 -= self.VEL  # Move second base image leftwards
        
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH  # Reset first base image position
            
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH  # Reset second base image position

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))  # Display first base image
        win.blit(self.IMG, (self.x2, self.y))  # Display second base image

def draw_window(win, birds, pipes, base, score, gen, high_score):
    win.blit(BG_IMG, (0, 0))  # Display background image
    
    for pipe in pipes:
        pipe.draw(win)  # Draw pipes
        
    text = STAT_FONT.render("Score:" + str(score), 1, (255, 255, 255))  # Render score text
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))  # Display score text
    
    text = STAT_FONT.render("Gen:" + str(gen), 1, (255, 255, 255))  # Render generation text
    win.blit(text, (10, 10))  # Display generation text
    
    text = STAT_FONT.render("Highest Score:" + str(high_score), 1, (255, 255, 255))  # Render high score text
    win.blit(text, (70, 70))  # Display high score text
    
    base.draw(win)  # Draw base
    
    for bird in birds:
        bird.draw(win)  # Draw birds
        
    pygame.display.update()  # Update display

def main(genomes, config):
    global gen, high_score
    gen += 1  # Increment generation count
    nets = []  # Initialize neural networks list
    birds = []  # Initialize birds list
    ge = []  # Initialize genomes list
    
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)  # Create neural network for genome
        nets.append(net)  # Add network to list
        birds.append(Bird(230, 350))  # Add a new Bird instance to the birds list
        g.fitness = 0  # Initialize the fitness of the genome
        ge.append(g)  # Add genome to the list

    pipes = [Pipe(600)]  # Initialize a list of pipes with one Pipe instance
    base = Base(730)  # Create a Base instance
    clock = pygame.time.Clock()  # Create a Clock instance to control the game's frame rate
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Set up the game window
    
    score = 0  # Initialize the score
    
    run = True  # Set the game loop flag
    while run:
        clock.tick(30)  # Control the frame rate to 30 FPS
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Check for quit event
                run = False  # Exit the game loop
                pygame.quit()  # Quit pygame
                quit()  # Exit the program
                
        pipe_ind = 0  # Initialize the index of the closest pipe
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1  # Update the index if the first pipe is passed
        else:
            run = False  # Exit the game loop if no birds are left
            break
        
        for x, bird in enumerate(birds):
            bird.move()  # Move the bird
            ge[x].fitness += 0.1  # Increase the fitness of the genome
            
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                bird.jump()  # Make the bird jump if the neural network's output is greater than 0.5
                
        add_pipe = False  # Initialize flag to add a new pipe
        rem = []  # Initialize list to store pipes to be removed
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # ge[x].fitness -= 1  # Decrease fitness on collision
                    birds.pop(x)  # Remove the bird from the list
                    nets.pop(x)  # Remove the network from the list
                    ge.pop(x)  # Remove the genome from the list
                
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True  # Mark pipe as passed
                    add_pipe = True  # Set flag to add a new pipe
                
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)  # Add pipe to the removal list
                
            pipe.move()  # Move the pipe
            
        if add_pipe:
            score += 1  # Increment the score
            if score > high_score:
                high_score = score  # Update the highest score if current score os higher
            for g in ge:
                g.fitness += 5  # Increase fitness for passing a pipe
            pipes.append(Pipe(600))  # Add a new pipe
            
        for r in rem:
            pipes.remove(r)  # Remove pipes from the list
            
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)  # Remove the bird if it hits the ground or flies too high
                nets.pop(x)  # Remove the network from the list
                ge.pop(x)  # Remove the genome from the list
        
        base.move()  # Move the base
        draw_window(win, birds, pipes, base, score, gen, high_score)  # Draw the game window

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, 
                                config_path)  # Load NEAT configuration
    
    p = neat.Population(config)  # Create a population with the given configuration
    
    p.add_reporter(neat.StdOutReporter(True))  # Add a reporter to show progress in the console
    stats = neat.StatisticsReporter()  # Create a statistics reporter
    p.add_reporter(stats)  # Add the statistics reporter
    
    winner = p.run(main, 50)  # Run the NEAT algorithm for 50 generations

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)  # Get the directory of the current file
    config_path = os.path.join(local_dir, "config-feedforward.txt")  # Get the path to the config file
    run(config_path)  # Run the NEAT algorithm with the given config path
