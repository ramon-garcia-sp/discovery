def deserealize_service(data: list) -> list:
    response = []
    for item in data:
        response.append(
            {
                "id": item.id,
                "service_name": item.service_name,
                "owner_team": item.owner_team,
                "repository_source": item.repository_source,
                "lifecycle_status": item.lifecycle_status,
                "consolidation_confict": item.consolidation_confict,
                "last_updated": item.last_updated.isoformat(),
            }
        )
    return response