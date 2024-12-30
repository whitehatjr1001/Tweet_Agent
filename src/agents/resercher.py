from playwright.sync_api import sync_playwright
import json

# Function to scrape tweets by hashtag
def scrape_tweets_by_hashtag(hashtag, max_pages=1):
    """
    Scrape tweets from X.com using a specific hashtag.
    """
    tweets_data = []
    _xhr_calls = []

    def intercept_response(response):
        """
        Capture all background XHR requests and save relevant ones.
        """
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)  # Set to False for debugging
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Enable response interception
        page.on("response", intercept_response)

        # Go to the hashtag search page
        search_url = f"https://twitter.com/search?q=%23{hashtag}&src=typed_query&f=live"
        page.goto(search_url, wait_until="networkidle")
        
        try:
            # Wait for either the main content or login prompt
            page.wait_for_selector("article[data-testid='tweet']", timeout=10000)
        except:
            print("Could not find tweets directly, checking for login wall...")
            # If login wall appears, we need to handle authentication
            if page.locator("text=Log in").is_visible():
                print("Login required to view tweets")
                return []

        # Scroll down to load more tweets
        for _ in range(max_pages):
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2000)

        # Extract relevant XHR calls containing tweet data
        tweet_calls = [f for f in _xhr_calls if "TweetResultByRestId" in f.url]
        for xhr in tweet_calls:
            try:
                data = xhr.json()
                if 'data' in data and 'tweetResult' in data['data']:
                    tweets_data.append(data['data']['tweetResult']['result'])
            except Exception as e:
                print(f"Error parsing XHR data: {e}")

        browser.close()

    return tweets_data

# Function to parse tweets
def parse_tweets(raw_data):
    """
    Parse raw data from X.com to extract relevant fields.
    """
    parsed_tweets = []
    for tweet_data in raw_data:
        try:
            if 'legacy' in tweet_data:
                legacy_data = tweet_data['legacy']
                core_data = tweet_data.get('core', {})
                user_data = core_data.get('user_results', {}).get('result', {}).get('legacy', {})
                
                tweet = {
                    "text": legacy_data.get("full_text", ""),
                    "likes": legacy_data.get("favorite_count", 0),
                    "retweets": legacy_data.get("retweet_count", 0),
                    "views": tweet_data.get("views", {}).get("count", 0),
                    "created_at": legacy_data.get("created_at", ""),
                    "user": user_data.get("screen_name", "")
                }
                parsed_tweets.append(tweet)
                        .get("screen_name", "")
                }
                parsed_tweets.append(tweet)
        except Exception as e:
            print(f"Parsing error: {e}")
            continue
    return parsed_tweets

# Function to analyze and filter tweets with the most reach
def analyze_tweets(tweets, min_engagement=100):
    """
    Analyze tweets to find those with the most reach.
    """
    high_reach_tweets = [
        tweet for tweet in tweets if tweet["likes"] + tweet["retweets"] >= min_engagement
    ]
    # Sort tweets by total engagement
    high_reach_tweets.sort(key=lambda x: x["likes"] + x["retweets"], reverse=True)
    return high_reach_tweets

# Main function
def main():
    hashtag = "Tech"  # Target hashtag
    print(f"Scraping tweets for hashtag: #{hashtag}")

    raw_tweets = scrape_tweets_by_hashtag(hashtag, max_pages=2)
    parsed_tweets = parse_tweets(raw_tweets)

    if not parsed_tweets:
        print("No tweets found!")
        return

    print(f"Total tweets scraped: {len(parsed_tweets)}")
    high_reach_tweets = analyze_tweets(parsed_tweets)

    print(f"High reach tweets for #{hashtag}:")
    for tweet in high_reach_tweets[:10]:
        print(f"User: @{tweet['user']}")
        print(f"Tweet: {tweet['text']}")
        print(f"Engagement: {tweet['likes']} likes, {tweet['retweets']} retweets, {tweet['views']} views")
        print(f"Posted: {tweet['created_at']}")
        print("-" * 80)

if __name__ == "__main__":
    main()
