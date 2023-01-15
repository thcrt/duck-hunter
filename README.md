# duck hunter

this is a bot for Mastodon made to implement the classic IRC duck hunter game. remember the good ol' days on IRC, .bang'ing (or .bef'ing) ASCII ducks whenever they appeared? anyone? well,  guess it's just me, and [that one guy](https://xkcd.com/1782/). for the uninitiated, here's how it works:

1. the bot will post a ~~toot~~ status with an ASCII duck in it
2. the first person to reply to that status with an instruction to shoot (`bang!`) or befriend (`bef!`) that duck wins a point
3. after a random interval, another duck appears and the cycle repeats

you really had to make your own fun back then.

anyway, those of us who are chronically online can now be rewarded for having nothing better to do! just follow the bot [on its home instance](https://botsin.space/@duckhunter) and shoot/befriend any ducks you see. a leaderboard / stats tracking is coming Soon (tm).

for any questions, send me a message at [@amshepherd@mstdn.social](https://mstdn.social/@amshepherd) :)

## features
- four different animals
- a (small) chance that your rifle, or persuasive attempts, will fail
- a 60-second timeout should the above happen
- random ASCII art by hayley jane wakenshaw
- low API calls (update ticks once every 10 seconds)
- configurability

## TODO
- scorekeeping
- leaderboard webpage
- statistics
- variable success rate based on previous scores (beginner's luck)
- more animals
