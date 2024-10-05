import requests
import time
import sys
from datetime import datetime, timedelta
import argparse

class HackerOne:
    all_program_overview = []
    bbp_program_details = {}

    def get_all_program_overview(self):
        if not self.all_program_overview:
            self.fetch_all_program_overview()
        return self.all_program_overview
    
    def get_program_details(self, handle):
        if handle not in self.bbp_program_details.keys():
            self.fetch_program_details_by_handle(handle)
        return self.bbp_program_details[handle]

    def fetch_all_program_overview(self):
        base_url = "https://hackerone.com/programs/search"
        headers = {
            "Accept": "application/json"
        }
        all_results = []
        page = 1
        limit = 100  # Max results per page, typically 100 based on the description

        while True:
            try:
                # Set the query parameters with dynamic page number
                params = {
                    "query": "type:hackerone",
                    "sort": "published_at:descending",
                    "page": page
                }

                # Send the GET request
                response = requests.get(base_url, headers=headers, params=params)
                
                # Raise an error for bad responses
                response.raise_for_status()

                # Parse JSON response
                data = response.json()

                # Get relevant fields
                limit = data.get("limit", 0)
                total = data.get("total", 0)
                results = data.get("results", [])

                # Append current results to the main list
                all_results.extend(results)

                # Check if we have retrieved all results
                if len(all_results) >= total:
                    print(f"Total results fetched: {len(all_results)}")
                    break

                # Increment page number to fetch the next batch of results
                page += 1
                
                # Add a delay to prevent overwhelming the server with requests
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data from page {page}: {e}")
                break

        self.all_program_overview = all_results
        return True
    
    def fetch_program_details_by_handle(self, handle):
        url = f"https://hackerone.com/{handle}"
        headers = {
            "Accept": "application/json"
        }
        
        try:
            # Send the GET request
            response = requests.get(url, headers=headers)
            
            # Raise an error for bad HTTP status codes (4xx, 5xx)
            response.raise_for_status()
            
            # Attempt to parse the JSON response
            try:
                program_details = response.json()
            except ValueError:
                # Handle the case where the response isn't valid JSON
                print(f"Error: Response from {url} is not valid JSON.")
                return False
            
            # Update the program details in the class attribute
            self.bbp_program_details.update({handle: program_details})

        except requests.exceptions.RequestException as e:
            # Catch any requests-related errors
            print(f"Error fetching program details for {handle}: {e}")
            return False

        return True

    def get_bbp_handles(self):
        all_programs = self.get_all_program_overview()

        # Extract handles for programs that offer bounties
        bbp_handles = [
            d["handle"] 
            for d in all_programs 
            if d.get("meta", {}).get("offers_bounties", False)
        ]
        return bbp_handles

    def get_updated_programs_since_days(self, since_days=1):
        updated_programs = []
        bbp_handles = self.get_bbp_handles()
        total_count = len(bbp_handles)
        now = datetime.utcnow()  # Get the current time in UTC
        time_threshold = now - timedelta(days=since_days)  # Calculate the time threshold
        for count, handle in enumerate(bbp_handles):
            print(f"\rProgram {count}/{total_count}", end="")
            # Fetch program details
            program_details = self.get_program_details(handle)
            
            # Get the "last_policy_change_at" field, skip if not present
            last_policy_change_str = program_details.get("last_policy_change_at")
            
            if last_policy_change_str:
                try:
                    # Convert the "last_policy_change_at" string to a datetime object
                    last_policy_change = datetime.strptime(last_policy_change_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    # Check if the last policy change is within the given time range
                    if last_policy_change >= time_threshold:
                        updated_programs.append(handle)
                except ValueError:
                    # Handle potential issues with datetime formatting if necessary
                    print(f"Skipping {handle} due to invalid date format in 'last_policy_change_at'.")
        
        return updated_programs
    
    def get_program_csv(self, handle):
        program_details = self.get_program_details(handle)
        last_policy_change_str = program_details.get("last_policy_change_at")
        return(f"{last_policy_change_str},https://hackerone.com/{handle}\n")



def main(days):
    # Instantiate the HackerOne object
    hackerone = HackerOne()

    # Get all bug bounty program handles (list of programs offering bounties)
#    all_programs = hackerone.get_bbp_handles()

    # Get the recently updated programs
#    updated_programs = hackerone.get_updated_programs_since_days(days)
    updated_programs=['3cx', 'dyson', 'mercadolibre', 'trip_com', 'modern_treasury', 'gocardless_bbp', 'six-group', 'malwarebytes', 'amazonvrp', 'grab', 'brave', 'deriv', 'cloudflare']

    # Print the results
    if updated_programs:
        print(f"Programs updated in the last {days} days: {updated_programs}")
    else:
        print(f"No programs have been updated in the last {days} days.")
    with open("updated_programs.csv", "w") as f:
        for program in updated_programs:
            f.write(hackerone.get_program_csv(program))

if __name__ == "__main__":
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Fetch HackerOne programs updated within the last N days.")
    
    # Add an argument for the number of days
    parser.add_argument(
        "days",
        type=int,
        help="The number of days to check for recent program updates."
    )
    
    # Parse the arguments from the command line
    args = parser.parse_args()
    
    # Call the main function with the number of days from argparse
    main(args.days)




