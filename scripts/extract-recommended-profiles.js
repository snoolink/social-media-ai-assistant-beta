(async () => {
  // First, scroll to load all suggested profiles
  let scrollCount = 0;
  const maxScrolls = 20; // Limit scrolling to avoid infinite loops
  
  console.log("🔍 Starting to scrape 'Suggested for you' profiles...");
  
  // Scroll down the page to load more suggestions
  let prevHeight = document.body.scrollHeight;
  let sameCount = 0;
  
  while (scrollCount < maxScrolls) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, 2000)); // wait for new suggestions to load
    
    const newHeight = document.body.scrollHeight;
    if (newHeight === prevHeight) {
      sameCount++;
      if (sameCount > 3) break; // stop after multiple checks of no new content
    } else {
      sameCount = 0;
      prevHeight = newHeight;
    }
    scrollCount++;
    console.log(`📜 Scroll ${scrollCount}/${maxScrolls}`);
  }
  
  console.log("✅ Finished scrolling, extracting profiles...");
  
  // Extract all suggested profile links
  // Look for links in the "Suggested for you" section
  const suggestedProfiles = Array.from(
    document.querySelectorAll('a[href^="/"]')
  )
    .map(a => a.getAttribute('href'))
    .filter(href => {
      // Filter to get only profile URLs (format: /username/)
      if (!href) return false;
      const match = href.match(/^\/([^/]+)\/?$/);
      if (!match) return false;
      
      // Exclude non-profile paths
      const excludedPaths = ['explore', 'direct', 'p', 'reel', 'reels', 'tv', 
                             'stories', 'accounts', 'about', 'legal', 'privacy', 
                             'safety', 'help', 'press', 'api', 'jobs', 'terms'];
      const username = match[1];
      return !excludedPaths.includes(username);
    })
    .map(href => href.replace(/\//g, '')) // Remove slashes to get username
    .filter(Boolean);
  
  const uniqueProfiles = [...new Set(suggestedProfiles)];
  
  console.log(`✨ Found ${uniqueProfiles.length} unique suggested profiles`);
  console.log(uniqueProfiles);
  
  // // Create downloadable CSV
  // const csv = 'userName,url\n' + uniqueProfiles.map(u => `${u},https://www.instagram.com/${u}/`).join('\n');
  // const blob = new Blob([csv], { type: 'text/csv' });
  // const url = URL.createObjectURL(blob);
  // const a = document.createElement('a');
  // a.href = url;
  // a.download = 'suggested_profiles.csv';
  // a.click();
    // Create downloadable CSV with timestamp
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-').replace('T', '_');
  const csv = 'userName,url\n' + uniqueProfiles.map(u => `${u},https://www.instagram.com/${u}/`).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `suggested_profiles_${timestamp}.csv`;
  a.click();
  
  console.log("💾 CSV file downloaded as 'suggested_profiles.csv'");
  
  return uniqueProfiles;
})();