import random, string
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from g4f import BaseProvider, models, Provider

logging = True

def main():
    providers = get_providers()
    failed_providers = []

    for _provider in providers:
        if _provider.needs_auth:
            continue
        print("Provider:", _provider.__name__)
        result = test(_provider)
        print("Result:", result)
        if _provider.working and not result:
            failed_providers.append(_provider)

    print()

    if failed_providers:
        print(f"Failed providers:\n")
        for _provider in failed_providers:
            print(f"{_provider.__name__}")
    else:
        print(f"All providers are working")


def get_providers() -> list[type[BaseProvider]]:
    provider_names = dir(Provider)
    ignore_names = [
        "base_provider",
        "BaseProvider"
    ]
    provider_names = [
        provider_name
        for provider_name in provider_names
        if not provider_name.startswith("__") and provider_name not in ignore_names
    ]
    return [getattr(Provider, provider_name) for provider_name in sorted(provider_names)]


def create_response(_provider: type[BaseProvider], _str: str) -> str:
    if _provider.supports_gpt_35_turbo:
        model = models.gpt_35_turbo.name    
    elif _provider.supports_gpt_4:
        model = models.gpt_4
    elif hasattr(_provider, "model"):
        model = _provider.model
    else:
        model = None
    response = _provider.create_completion(
        model=model,
        messages=[{"role": "user", "content": f"just output \"{_str}\""}],
        stream=False,
    )
    return "".join(response)

    
def test(_provider: type[BaseProvider]) -> bool:
    try:
        _str = "".join(random.choices(string.ascii_letters + string.digits, k=4))
        response = create_response(_provider, _str)
        assert type(response) is str
        assert len(response) > 0 and _str in response
        return response
    except Exception as e:
        if logging:
            print(f"{_provider.__name__}: {str(e)}")
        return False


if __name__ == "__main__":
    main()
