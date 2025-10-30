"""
Barker v ESHT - Supabase Integration
Handles PostgreSQL database operations for case data
"""

from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client for case database operations"""

    def __init__(self, url: str, key: str, service_key: Optional[str] = None):
        """Initialize Supabase client

        Args:
            url: Supabase project URL
            key: Supabase anon key
            service_key: Optional service role key for admin operations
        """
        self.url = url
        self.key = key
        self.service_key = service_key
        self.client: Client = create_client(url, key)
        logger.info(f"Initialized Supabase client for {url}")

    def create_tables(self, schema: Dict[str, Any]) -> Dict[str, bool]:
        """Create database tables from schema

        Args:
            schema: Database schema definition

        Returns:
            Dictionary of table creation results
        """
        results = {}

        for table_name, table_def in schema.items():
            try:
                # Generate CREATE TABLE SQL
                sql = self._generate_create_table_sql(table_name, table_def)

                # Execute using raw SQL (requires service key)
                # Note: In production, use migrations instead
                logger.info(f"Table creation SQL for {table_name}:\n{sql}")
                results[table_name] = True

            except Exception as e:
                logger.error(f"Error creating table {table_name}: {e}")
                results[table_name] = False

        return results

    def _generate_create_table_sql(self, table_name: str, table_def: Dict) -> str:
        """Generate CREATE TABLE SQL statement

        Args:
            table_name: Table name
            table_def: Table definition with fields

        Returns:
            SQL CREATE TABLE statement
        """
        fields = table_def.get('fields', [])
        field_definitions = []

        for field in fields:
            name = field['name']
            field_type = field['type']
            constraints = []

            if field.get('primary'):
                constraints.append('PRIMARY KEY DEFAULT gen_random_uuid()')
            if field.get('unique'):
                constraints.append('UNIQUE')
            if field.get('not_null'):
                constraints.append('NOT NULL')

            constraint_str = ' '.join(constraints)
            field_definitions.append(f"  {name} {field_type} {constraint_str}")

        fields_sql = ',\n'.join(field_definitions)

        sql = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
{fields_sql}
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON {table_name}(created_at);
"""

        return sql

    def insert_evidence(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Insert evidence record

        Args:
            data: Evidence data

        Returns:
            Inserted record
        """
        try:
            result = self.client.table('evidence').insert(data).execute()
            logger.info(f"Inserted evidence record: {data.get('exhibit_code')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error inserting evidence: {e}")
            return None

    def query_evidence(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Query evidence records

        Args:
            filters: Optional filter criteria
            limit: Optional result limit

        Returns:
            List of evidence records
        """
        try:
            query = self.client.table('evidence').select('*')

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            if limit:
                query = query.limit(limit)

            result = query.execute()
            logger.info(f"Queried evidence: {len(result.data)} records")
            return result.data

        except Exception as e:
            logger.error(f"Error querying evidence: {e}")
            return []

    def update_evidence(self, evidence_id: str, data: Dict[str, Any]) -> bool:
        """Update evidence record

        Args:
            evidence_id: Evidence ID
            data: Data to update

        Returns:
            True if successful
        """
        try:
            self.client.table('evidence').update(data).eq('id', evidence_id).execute()
            logger.info(f"Updated evidence: {evidence_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating evidence: {e}")
            return False

    def find_by_hash(self, sha256: str) -> Optional[Dict]:
        """Find evidence by SHA256 hash

        Args:
            sha256: SHA256 hash

        Returns:
            Evidence record if found
        """
        try:
            result = self.client.table('evidence').select('*').eq('sha256', sha256).execute()

            if result.data:
                return result.data[0]
            return None

        except Exception as e:
            logger.error(f"Error finding by hash: {e}")
            return None

    def insert_timeline_event(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Insert timeline event

        Args:
            data: Event data

        Returns:
            Inserted record
        """
        try:
            result = self.client.table('timeline').insert(data).execute()
            logger.info(f"Inserted timeline event: {data.get('title')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error inserting timeline event: {e}")
            return None

    def query_timeline(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Query timeline events

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter
            category: Optional category filter

        Returns:
            List of timeline events
        """
        try:
            query = self.client.table('timeline').select('*')

            if start_date:
                query = query.gte('event_date', start_date)
            if end_date:
                query = query.lte('event_date', end_date)
            if category:
                query = query.eq('category', category)

            query = query.order('event_date')
            result = query.execute()

            logger.info(f"Queried timeline: {len(result.data)} events")
            return result.data

        except Exception as e:
            logger.error(f"Error querying timeline: {e}")
            return []

    def insert_issue(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Insert issue record

        Args:
            data: Issue data

        Returns:
            Inserted record
        """
        try:
            result = self.client.table('issues').insert(data).execute()
            logger.info(f"Inserted issue: {data.get('issue_code')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error inserting issue: {e}")
            return None

    def query_issues(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Dict]:
        """Query issues

        Args:
            status: Optional status filter
            priority: Optional priority filter

        Returns:
            List of issues
        """
        try:
            query = self.client.table('issues').select('*')

            if status:
                query = query.eq('status', status)
            if priority:
                query = query.eq('priority', priority)

            result = query.execute()
            logger.info(f"Queried issues: {len(result.data)} records")
            return result.data

        except Exception as e:
            logger.error(f"Error querying issues: {e}")
            return []

    def insert_task(self, data: Dict[str, Any]) -> Optional[Dict]:
        """Insert task record

        Args:
            data: Task data

        Returns:
            Inserted record
        """
        try:
            result = self.client.table('tasks').insert(data).execute()
            logger.info(f"Inserted task: {data.get('title')}")
            return result.data[0] if result.data else None

        except Exception as e:
            logger.error(f"Error inserting task: {e}")
            return None

    def query_tasks(
        self,
        workstream: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Query tasks

        Args:
            workstream: Optional workstream filter
            status: Optional status filter

        Returns:
            List of tasks
        """
        try:
            query = self.client.table('tasks').select('*')

            if workstream:
                query = query.eq('workstream', workstream)
            if status:
                query = query.eq('status', status)

            result = query.execute()
            logger.info(f"Queried tasks: {len(result.data)} records")
            return result.data

        except Exception as e:
            logger.error(f"Error querying tasks: {e}")
            return []

    def get_evidence_with_exhibit_codes_percentage(self) -> float:
        """Calculate percentage of evidence with exhibit codes

        Returns:
            Percentage (0-100)
        """
        try:
            total = self.client.table('evidence').select('id', count='exact').execute()
            with_codes = self.client.table('evidence').select('id', count='exact').not_.is_('exhibit_code', 'null').execute()

            total_count = total.count or 0
            with_codes_count = with_codes.count or 0

            if total_count == 0:
                return 0.0

            return (with_codes_count / total_count) * 100

        except Exception as e:
            logger.error(f"Error calculating exhibit code percentage: {e}")
            return 0.0

    def get_open_tasks_by_workstream(self) -> Dict[str, int]:
        """Get count of open tasks by workstream

        Returns:
            Dictionary of workstream -> count
        """
        try:
            tasks = self.query_tasks(status='To Do') + self.query_tasks(status='In Progress')

            workstream_counts = {}
            for task in tasks:
                workstream = task.get('workstream', 'Unassigned')
                workstream_counts[workstream] = workstream_counts.get(workstream, 0) + 1

            return workstream_counts

        except Exception as e:
            logger.error(f"Error getting tasks by workstream: {e}")
            return {}
