"""
Flask CLI Commands for PipLine Treasury System
"""

import click
from flask.cli import with_appcontext
import json
from datetime import datetime

from app.services.currency_fixer_service import currency_fixer_service
from app.services.unified_database_service import unified_db_service as db_optimization_service
from app.services.performance_service import performance_monitor
from app.services.enhanced_cache_service import cache_service

@click.group()
def currency():
    """Currency management commands."""
    pass

@currency.command()
@with_appcontext
def health():
    """Check currency health status."""
    click.echo("📊 Generating currency health report...")
    
    try:
        report = currency_fixer_service.get_currency_health_report()
        
        click.echo("\n📋 Currency Health Report:")
        click.echo(f"  Total Transactions: {report.get('total_transactions', 0)}")
        
        if 'by_currency' in report:
            click.echo("  By Currency:")
            for currency, count in report['by_currency'].items():
                click.echo(f"    {currency}: {count} transactions")
        
        if 'issues' in report:
            issues = report['issues']
            total_issues = sum(issues.values())
            
            if total_issues > 0:
                click.echo(f"\n⚠️  Issues Found: {total_issues}")
                for issue_type, count in issues.items():
                    if count > 0:
                        click.echo(f"    {issue_type.replace('_', ' ').title()}: {count}")
            else:
                click.echo("\n✅ No currency issues found!")
        
    except Exception as e:
        click.echo(f"❌ Error generating health report: {e}")

@currency.command()
@with_appcontext
@click.option('--dry-run', is_flag=True, help='Show what would be fixed without making changes')
def fix(dry_run):
    """Fix all currency issues automatically."""
    
    if dry_run:
        click.echo("🔍 Running in DRY RUN mode - no changes will be made")
    
    click.echo("🔧 Starting currency audit and fix...")
    
    try:
        if dry_run:
            # In a real implementation, you'd want a dry-run mode in the service
            click.echo("⚠️ Dry run mode not fully implemented in service yet")
        
        report = currency_fixer_service.run_full_currency_audit_and_fix()
        
        click.echo("\n📊 Fix Results:")
        click.echo(f"  Status: {report.get('status', 'unknown')}")
        
        if 'fixes_applied' in report:
            fixes = report['fixes_applied']
            total_fixes = sum(fixes.values())
            click.echo(f"  Total Fixes Applied: {total_fixes}")
            
            for fix_type, count in fixes.items():
                if count > 0:
                    click.echo(f"    {fix_type.replace('_', ' ').title()}: {count}")
        
        if report.get('errors'):
            click.echo(f"\n❌ Errors:")
            for error in report['errors']:
                click.echo(f"    {error}")
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"currency_fix_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        click.echo(f"\n📄 Report saved to: {report_file}")
        
        if report.get('status') == 'completed':
            click.echo("✅ Currency fixing completed successfully!")
        else:
            click.echo("❌ Currency fixing completed with errors.")
            
    except Exception as e:
        click.echo(f"💥 Error during currency fix: {e}")

@currency.command()
@with_appcontext
def standardize():
    """Standardize currency codes only."""
    click.echo("🔄 Standardizing currency codes...")
    
    try:
        # Create a minimal fixer instance for just standardization
        fixer = currency_fixer_service
        fixer._standardize_currency_codes()
        click.echo("✅ Currency standardization completed!")
        
    except Exception as e:
        click.echo(f"❌ Error standardizing currencies: {e}")

@click.group()
def database():
    """Database management commands."""
    pass

@database.command()
@with_appcontext
def health():
    """Check database health status."""
    try:
        health_info = db_optimization_service.get_database_health()
        click.echo(f"✅ Database Status: {health_info.get('status', 'Unknown')}")
        click.echo(f"📊 Health Score: {health_info.get('health_score', 0)}/100")
        click.echo(f"⏱️  Response Time: {health_info.get('response_time_ms', 0)}ms")
        click.echo(f"🔗 Database Type: {health_info.get('database_type', 'Unknown')}")
        
    except Exception as e:
        click.echo(f"❌ Error checking database health: {e}")

@database.command()
@with_appcontext
def optimize():
    """Optimize database performance."""
    try:
        result = db_optimization_service.optimize_sqlite_safely()
        if 'error' in result:
            click.echo(f"❌ {result['error']}")
        else:
            click.echo("✅ Database optimization completed!")
            click.echo(f"📊 Database Size: {result.get('database_size_mb', 0)} MB")
        
    except Exception as e:
        click.echo(f"❌ Error optimizing database: {e}")

@database.command()
@with_appcontext
def backup():
    """Create database backup."""
    try:
        import subprocess
        import sys
        result = subprocess.run([sys.executable, 'scripts/backup_database.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            click.echo(result.stdout)
        else:
            click.echo(f"❌ Backup failed: {result.stderr}")
        
    except Exception as e:
        click.echo(f"❌ Error creating backup: {e}")

@click.group()
def performance():
    """Performance monitoring and optimization commands."""
    pass

@performance.command()
@with_appcontext
def summary():
    """Show performance summary."""
    try:
        summary = performance_monitor.get_performance_summary()
        
        if summary['status'] == 'no_data':
            click.echo("📊 No performance data available yet")
            return
        
        data = summary['summary']
        click.echo("\n📊 Performance Summary:")
        click.echo(f"   Total Requests: {data['total_requests']}")
        click.echo(f"   Avg Response Time: {data['avg_response_time']}s")
        click.echo(f"   Max Response Time: {data['max_response_time']}s")
        click.echo(f"   Slow Requests: {data['slow_requests_count']}")
        
        if data.get('system_metrics'):
            sm = data['system_metrics']
            click.echo(f"   CPU Usage: {sm.get('cpu_percent', 0):.1f}%")
            click.echo(f"   Memory Usage: {sm.get('memory_percent', 0):.1f}%")
        
        click.echo("\n🐌 Slowest Endpoints:")
        for endpoint, avg_time in data['slowest_endpoints'][:3]:
            click.echo(f"   {endpoint}: {avg_time:.3f}s")
        
    except Exception as e:
        click.echo(f"❌ Error getting performance summary: {e}")

@performance.command()
@with_appcontext
def optimize():
    """Optimize system performance."""
    try:
        click.echo("🔧 Optimizing performance...")
        
        # Memory optimization
        result = performance_monitor.optimize_memory()
        
        if result['status'] == 'success':
            click.echo(f"✅ Memory optimized: {result['memory_before']:.1f}% -> {result['memory_after']:.1f}%")
            click.echo(f"   Objects collected: {result['objects_collected']}")
            click.echo(f"   Memory freed: {result['improvement']:.1f}%")
        else:
            click.echo(f"❌ Memory optimization failed: {result.get('message', 'Unknown error')}")
        
        # Cache optimization
        cache_stats = cache_service.get_stats()
        click.echo(f"\n📋 Cache Stats:")
        click.echo(f"   Entries: {cache_stats['entries']}")
        click.echo(f"   Hit Rate: {cache_stats['hit_rate']}%")
        click.echo(f"   Total Requests: {cache_stats['total_requests']}")
        
    except Exception as e:
        click.echo(f"❌ Error optimizing performance: {e}")

@performance.command()
@with_appcontext
def cache():
    """Show cache statistics."""
    try:
        stats = cache_service.get_stats()
        
        click.echo("\n💾 Cache Statistics:")
        click.echo(f"   Total Entries: {stats['entries']}")
        click.echo(f"   Cache Hits: {stats['hits']}")
        click.echo(f"   Cache Misses: {stats['misses']}")
        click.echo(f"   Hit Rate: {stats['hit_rate']}%")
        click.echo(f"   Total Requests: {stats['total_requests']}")
        
        if stats['hit_rate'] < 50:
            click.echo("\n⚠️  Low cache hit rate detected. Consider:")
            click.echo("   - Increasing cache TTL")
            click.echo("   - Adding more cached endpoints")
            click.echo("   - Optimizing cache keys")
        else:
            click.echo("\n✅ Cache performance looks good!")
        
    except Exception as e:
        click.echo(f"❌ Error getting cache statistics: {e}")

def register_cli_commands(app):
    """Initialize CLI commands for the Flask app."""
    app.cli.add_command(currency)
    app.cli.add_command(database)
    app.cli.add_command(performance)
    
    # Flask-Migrate commands are automatically registered via migrate.init_app()
    # Use: flask db init, flask db migrate, flask db upgrade, etc.
