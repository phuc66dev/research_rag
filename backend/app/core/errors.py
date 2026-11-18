from typing import NoReturn

from fastapi import HTTPException


def not_implemented(feature: str) -> NoReturn:
    raise HTTPException(
        status_code=501,
        detail={
            "code": "not_implemented",
            "message": f"{feature} chưa được triển khai trong bootstrap.",
        },
    )
