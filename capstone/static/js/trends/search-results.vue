<template>
  <div v-if="showLoading" ref="loadingMessage" tabindex="-1" class="results-list-container d-flex align-items-center">
    <span class="spinner-border spinner-border-sm mr-2"
          role="status"
          aria-hidden="true"></span>
    Loading example cases ...
  </div>
  <div v-else-if="error" class="results-list-container">
    {{error}}
  </div>
  <div v-else-if="results" class="results-list-container">
    <h2 ref="casesHeader" tabindex="-1">Example cases</h2>
    <p>Cases matching "{{term}}" in {{startYear}}<span v-if="startYear !== endYear">-{{endYear}}</span>:</p>
    <ul v-if="results.length" class="results-list">
      <case-result v-for="result in results"
                   :result="result"
                   :key="result.id">
      </case-result>
    </ul>
    <p v-else>No results found.</p>
    <div class="text-right">
      <a :href="searchPageUrl(this.term, this.startYear)">
        <span v-if="results.length >= 5">
          View more
        </span>
        <span v-else>
          View search page
        </span>
        >>
      </a>
    </div>
    <p class="text-muted font-italic">
      Note: because of differences in tokenization, search results may not exactly match graph counts.
    </p>
  </div>
</template>

<script>
  import CaseResult from '../search/case-result.vue';
  import {getApiUrl, jsonQuery} from '../api';
  import {encodeQueryData} from '../utils';
  import Vue from 'vue';

  export default {
    components: {
      CaseResult,
    },
    props: [
      'urls'
    ],
    data() {
      return {
        showLoading: false,
        error: null,
        results: null,
        params: null,
        term: null,
        startYear: null,
        endYear: null,
      }
    },
    methods: {
      search(term, params, startYear, endYear) {
        if (params.q.startsWith('api(')) {
          var searchParams = this.params = {
            decision_date__gte: [`${startYear}`],
            decision_date__lt: [`${endYear+1}`],
            page_size: [5],
          };

          var qParams = new URLSearchParams(params.q.slice(4, -1));
          for (let [key, val] of qParams.entries()) {
            if (key !== 'jurisdiction' || !(params.jurisdiction && params.jurisdiction !== "total")) {
              if (!(key in searchParams)) {
                searchParams[key] = [val];
              } else {
                searchParams[key].push(val);
              }
            }
          }
        } else {
          searchParams = this.params = {
            search: `"${params.q}"`,
            decision_date_min: `${startYear}-01-01`,
            decision_date_max: `${endYear}-12-31`,
            page_size: 5,
          };
        }
        if (params.jurisdiction && params.jurisdiction !== "total")
          searchParams.jurisdiction = params.jurisdiction;
        this.showLoading = true;
        Vue.nextTick().then(() => { this.$refs.loadingMessage.focus() });
        this.error = null;
        const url = getApiUrl(urls.api_root,"cases", searchParams, true);  // eslint-disable-line
        jsonQuery(url).then((resp)=>{
          this.results = resp.results;
          this.term = term;
          this.startYear = startYear;
          this.endYear = endYear;
          this.showLoading = false;
          Vue.nextTick().then(() => { this.$refs.casesHeader.focus() });
        }).catch(() => {
          // error handling
          this.showLoading = false;
          this.error = "Error loading examples."
        });
      },
      searchPageUrl(term, startYear) {
        var searchString = "";
        if (term.indexOf('api(') !== -1) {
          var searchParams = this.params = {
            decision_date__gte: `${startYear}`,
            decision_date__lt: `${startYear + 1}`,
          };
          searchString += new URLSearchParams(searchParams).toString() + '&';

          var api_command = term.split('api(')[1].slice(0, -1);
          searchString += api_command;

          return `${this.urls.api_root}cases/?${searchString}`
        } 

        return `${this.urls.search_page}?${encodeQueryData(this.params)}`
      },
      reset() {
        this.showLoading = false;
        this.error = null;
        this.results = null;
      },
    }
  }
</script>
