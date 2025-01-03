# NBAdle

NBAdle is a Wordle-inspired web application for NBA enthusiasts. The goal of the game is to guess an NBA player within a limited number of attempts based on various clues.

## Features

- **Interactive Gameplay**: Players guess NBA players using a user-friendly interface.
- **Dynamic Hints**: Feedback is provided on each guess, highlighting correct attributes (e.g., team, conference, position, etc.).
- **Player/Team Details**: Clickable player/team names display more detailed stats and information.
- **Stylish Visualizations**: Data and feedback are presented using dynamic visualizations, powered by Plotly.js.

## Tech Stack

- **Frontend**: React (with Vite for fast development and build).
- **Backend**: Flask for API development.
- **Database**: PostgreSQL to store player and team data.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/NBAdle.git
   cd nba_stats
   ```
2. Install dependencies for the frontend:
   ```bash
   cd frontend
   npm install
   ```
3. Start the frontend server:
   ```bash
   cd ../frontend
   npm run dev
   ```

## Gameplay Overview

1. The player has a limited number of guesses to identify the correct NBA player.
2. After each guess, the app provides feedback based on the player's attributes such as:
   - Team
   - Conference (Eastern/Western)
   - Position
   - Jersey Number
3. Correct attributes are visually highlighted, guiding the player toward the right answer.

## Acknowledgments

This project was inspired by the popular Wordle game and tailored for NBA fans. It leverages the following technologies:

- React and Vite for a smooth user experience.
- Flask and PostgreSQL for robust backend functionality.
- Plotly.js for visually appealing data presentation.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For inquiries or feedback, feel free to contact me via nbadle710@gmail.com.

