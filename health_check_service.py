"""
Simple Health Check Service
Uses httpx for HTTP requests and pydantic for data validation
"""

import asyncio
from datetime import datetime
from typing import List, Optional

import httpx
from pydantic import BaseModel, HttpUrl, Field, validator


class HealthCheckTarget(BaseModel):
    """Model for a health check target endpoint"""
    name: str = Field(..., min_length=1, max_length=100)
    url: HttpUrl
    timeout: int = Field(default=5, ge=1, le=60)
    expected_status: int = Field(default=200, ge=100, le=599)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('name cannot be empty or whitespace')
        return v.strip()


class HealthCheckResult(BaseModel):
    """Model for health check result"""
    target_name: str
    url: str
    status: str  # 'healthy', 'unhealthy', 'error'
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckService:
    """Service to perform health checks on multiple endpoints"""
    
    def __init__(self, targets: List[HealthCheckTarget]):
        self.targets = targets
    
    async def check_endpoint(self, target: HealthCheckTarget) -> HealthCheckResult:
        """Check a single endpoint"""
        start_time = datetime.utcnow()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    str(target.url),
                    timeout=target.timeout,
                    follow_redirects=True
                )
                
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                is_healthy = response.status_code == target.expected_status
                
                return HealthCheckResult(
                    target_name=target.name,
                    url=str(target.url),
                    status='healthy' if is_healthy else 'unhealthy',
                    status_code=response.status_code,
                    response_time_ms=round(response_time, 2),
                    checked_at=start_time
                )
        
        except httpx.TimeoutException:
            return HealthCheckResult(
                target_name=target.name,
                url=str(target.url),
                status='error',
                error_message=f'Request timeout after {target.timeout}s',
                checked_at=start_time
            )
        
        except httpx.RequestError as e:
            return HealthCheckResult(
                target_name=target.name,
                url=str(target.url),
                status='error',
                error_message=f'Request error: {str(e)}',
                checked_at=start_time
            )
        
        except Exception as e:
            return HealthCheckResult(
                target_name=target.name,
                url=str(target.url),
                status='error',
                error_message=f'Unexpected error: {str(e)}',
                checked_at=start_time
            )
    
    async def check_all(self) -> List[HealthCheckResult]:
        """Check all configured endpoints concurrently"""
        tasks = [self.check_endpoint(target) for target in self.targets]
        results = await asyncio.gather(*tasks)
        return list(results)
    
    def print_results(self, results: List[HealthCheckResult]) -> None:
        """Print health check results in a readable format"""
        print("\n" + "="*70)
        print("HEALTH CHECK RESULTS")
        print("="*70)
        
        for result in results:
            status_symbol = "✓" if result.status == 'healthy' else "✗"
            print(f"\n{status_symbol} {result.target_name}")
            print(f"  URL: {result.url}")
            print(f"  Status: {result.status.upper()}")
            
            if result.status_code:
                print(f"  HTTP Status: {result.status_code}")
            
            if result.response_time_ms:
                print(f"  Response Time: {result.response_time_ms}ms")
            
            if result.error_message:
                print(f"  Error: {result.error_message}")
            
            print(f"  Checked At: {result.checked_at.isoformat()}")
        
        print("\n" + "="*70)
        
        healthy_count = sum(1 for r in results if r.status == 'healthy')
        total_count = len(results)
        print(f"Summary: {healthy_count}/{total_count} endpoints healthy")
        print("="*70 + "\n")


async def main():
    """Example usage of the health check service"""
    
    # Define targets to check
    targets = [
        HealthCheckTarget(
            name="Google",
            url="https://www.google.com",
            timeout=10,
            expected_status=200
        ),
        HealthCheckTarget(
            name="GitHub API",
            url="https://api.github.com",
            timeout=10,
            expected_status=200
        ),
        HealthCheckTarget(
            name="Example (should fail)",
            url="https://httpstat.us/500",
            timeout=10,
            expected_status=200
        ),
    ]
    
    # Create service and run checks
    service = HealthCheckService(targets)
    results = await service.check_all()
    
    # Print results
    service.print_results(results)
    
    # Return results for programmatic use
    return results


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
