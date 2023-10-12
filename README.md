# OmitMe
Your Privacy-Centric, Easily Extendable Data Deletion Solution. 

![gif of cli](https://files.catbox.moe/4c5xsn.gif)

## Install
```
pip install omitme
```
May need to have chrome installed to function.

## Usage
```
omitme-cli --help
```

### Example
```bash
omitme-cli discord login
omitme-cli discord accounts
omitme-cli discord target messages-delete-all --account account_name
```

## Tested on
- Linux ✅
- Windows ❌
- MacOS ❌

### Supported platforms
#### Working
- Discord
- Reddit

#### Planned
- Matrix
- Twitter

## In-progress
- Work in progress GUI for Linux, MacOS & Windows.
    ![GUI](https://i.imgur.com/TOzXUdZ.png)

## Contributing
Omitme is built to be expandable to other platforms.

See an example [here](omitme/platforms/discord.py)

### The `Platform` class
Each new platform, show inherit from `Platform`.

```python
class Discord(Platform):
```

Each platform class requires some metadata.
`icon` should be stored in `omitme/resources/platforms`

```python
class Discord(Platform):
    api_url = "https://discord.com/api/v9"
    login_url = "https://discord.com/login"
    alias = "discord"
    icon = "discord.png"
    description = "Manage your discord data"
```

### Login

Each platform requires a login handler like so.

`driver` is a instance of [seleniumwire's webdriver](https://github.com/wkeeling/selenium-wire)

```python
@login
async def handle_login(
    self, driver: webdriver.Chrome, accounts: Accounts
) -> httpx.AsyncClient:
    pass
```

Once login is successful, the account should be stored safely using `accounts.add` & your custom HTTPX session should be returned.

```python
@login
async def handle_login(
    self, driver: webdriver.Chrome, accounts: Accounts
) -> httpx.AsyncClient:
    driver.get(self.login_url)

    ...

    await accounts.add(resp.json()["username"], session={"headers": headers})

    return session
```

### Targets
Targets are the methods called when a user wants to omit something, e.g. `omitme-cli reddit target posts-delete-all`, `posts-delete-all` would be our target.

#### Events
- `CheckingEvent`, API call in progress.
- `OmittedEvent`, data has been omitted.
- `CompletedEvent`, the omitting process is complete.

```python
@target("posts delete all", description="Delete all reddit posts")
async def handle_delete_posts(
    self, session: httpx.AsyncClient
) -> AsyncIterator[OmittedEvent | CheckingEvent | FailEvent | CompletedEvent]:
    resp = await session.get(
        f"/user/{await self._get_username(session)}/submitted",
        params={"timeframe": "all", "limit": "100"},
    )

    for post in resp.json()["data"]["children"]:
        await self._delete_post(session, post["kind"], post["data"]["id"])

        yield OmittedEvent(
            channel=post["data"]["subreddit"], content=post["data"]["selftext"]
        )

    yield CompletedEvent()
```
