import pandas as pd

# Read the CSV files
followings = pd.read_csv('profiles-data/snoolink_following.csv')
followers = pd.read_csv('profiles-data/snoolink_followers_1-420.csv')

# Strip whitespace from column names
followings.columns = followings.columns.str.strip()
followers.columns = followers.columns.str.strip()

# Get the set of usernames from followers
followers_set = set(followers['userName'].str.strip())

# Filter followings to find users not in followers
unfollow_list = followings[~followings['userName'].str.strip().isin(followers_set)]

# Save to new CSV
unfollow_list.to_csv('unfollow_list.csv', index=False)

print(f"Total followings: {len(followings)}")
print(f"Total followers: {len(followers)}")
print(f"Users to unfollow: {len(unfollow_list)}")
print(f"\nUnfollow list saved to 'unfollow_list.csv'")