We will continue to check out other test cases. \
  1. Make sure all playwright test run in the future must have the current directory as src/frontend\
  2. run playwright test case "select and delete a flow" with " 2>&1 | tee test-output.log" to output in console and a log file. There should be at least 5min
  time out to get each test case to run as it takes 2 min to just start the services.\
  3. analyze the test-output.log to see if there is any error\
  4. For any error, compare with src/frontend code base and see if we can fix that



npx playwright test tests/core/features/auto-login-off.spec.ts --project=chromium 2>&1 | tee test-output.log